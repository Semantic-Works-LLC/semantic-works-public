// Live transcript: the microphone goes into Apple's on-device speech model
// (SpeechAnalyzer, macOS 26+). What you say shows in a box under the bubble,
// keeping about the last 30 seconds, and every finished sentence is saved
// with its time to a text file. Nothing leaves the Mac.

import AppKit
import AVFoundation
import Speech

/// One stretch of recognized speech, timed on the host clock.
struct Caption {
    let start: CMTime
    let end: CMTime
    let text: String
    let isFinal: Bool
}

// MARK: - Microphone

final class Microphone: NSObject, AVCaptureAudioDataOutputSampleBufferDelegate {
    private let session = AVCaptureSession()
    private let queue = DispatchQueue(label: "bubblehead.mic", qos: .userInitiated)
    var onBuffer: ((CMSampleBuffer) -> Void)?   // called on the mic queue

    func start() {
        queue.async {
            if self.session.inputs.isEmpty {
                guard let device = AVCaptureDevice.default(for: .audio),
                      let input = try? AVCaptureDeviceInput(device: device) else { return }
                let output = AVCaptureAudioDataOutput()
                output.setSampleBufferDelegate(self, queue: self.queue)
                self.session.beginConfiguration()
                if self.session.canAddInput(input) { self.session.addInput(input) }
                if self.session.canAddOutput(output) { self.session.addOutput(output) }
                self.session.commitConfiguration()
            }
            self.session.startRunning()
        }
    }

    func stop() { queue.async { self.session.stopRunning() } }

    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer,
                       from connection: AVCaptureConnection) {
        onBuffer?(sampleBuffer)
    }
}

// MARK: - Speech recognizer

@available(macOS 26, *)
final class Captioner: @unchecked Sendable {
    /// Called on the main thread with every partial and final result.
    var onCaption: ((Caption) -> Void)?
    /// Called on the main thread with status such as "Downloading speech model…".
    var onStatus: ((String) -> Void)?

    private var analyzer: SpeechAnalyzer?
    private var input: AsyncStream<AnalyzerInput>.Continuation?
    private var outFormat: AVAudioFormat?
    private var converter: AVAudioConverter?
    private var stamped = false     // guarded by lock
    private var paused = false      // guarded by lock
    private var started = false
    private let lock = NSLock()

    /// Pausing stops feeding audio to the model.
    func setPaused(_ p: Bool) {
        let analyzer: SpeechAnalyzer? = lock.withLock {
            paused = p
            // After a pause the next buffer is stamped again, so the model
            // skips the gap instead of shifting later words earlier.
            if !p { stamped = false }
            return self.analyzer
        }
        // Turn whatever was still being recognized into final text.
        if p, let a = analyzer { Task { try? await a.finalize(through: nil) } }
    }

    func start() {
        guard !started else { return }
        started = true
        Task {
            do { try await run() } catch {
                NSLog("BubbleHead: transcript failed: %@", "\(error)")
                status("Transcript stopped: \(error.localizedDescription)")
            }
        }
    }

    private func status(_ s: String) {
        DispatchQueue.main.async { self.onStatus?(s) }
    }

    private func run() async throws {
        let locale = await SpeechTranscriber.supportedLocale(equivalentTo: Locale.current)
            ?? Locale(identifier: "en-US")
        let transcriber = SpeechTranscriber(locale: locale, preset: .progressiveTranscription)
        if let req = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
            status("Downloading speech model…")
            try await req.downloadAndInstall()
        }
        let format = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber])
        let (stream, continuation) = AsyncStream<AnalyzerInput>.makeStream()
        let analyzer = SpeechAnalyzer(modules: [transcriber])
        lock.withLock {
            self.outFormat = format
            self.input = continuation
            self.analyzer = analyzer
        }
        try await analyzer.start(inputSequence: stream)
        status("")
        NSLog("BubbleHead: transcript running (%@)", locale.identifier)

        for try await r in transcriber.results {
            let c = Caption(start: r.range.start, end: r.range.end,
                            text: String(r.text.characters), isFinal: r.isFinal)
            DispatchQueue.main.async { self.onCaption?(c) }
        }
    }

    /// Called on the mic queue with each microphone buffer.
    func append(_ sb: CMSampleBuffer) {
        guard let (out, cont, first) = lock.withLock({ () -> (AVAudioFormat, AsyncStream<AnalyzerInput>.Continuation, Bool)? in
            guard let f = outFormat, let c = input, !paused else { return nil }
            let first = !stamped
            stamped = true
            return (f, c, first)
        }) else { return }
        guard let pcm = Self.pcmBuffer(from: sb) else { return }
        // Only the first buffer carries a time (the capture clock); the analyzer
        // counts samples from there. Stamping every buffer fails with
        // "Audio input timestamp overlaps or precedes prior audio input",
        // because capture times and converted sample counts drift slightly.
        let start: CMTime? = first ? CMSampleBufferGetPresentationTimeStamp(sb) : nil

        if pcm.format == out {
            cont.yield(AnalyzerInput(buffer: pcm, bufferStartTime: start))
            return
        }
        if converter == nil || converter?.inputFormat != pcm.format {
            converter = AVAudioConverter(from: pcm.format, to: out)
        }
        guard let conv = converter else { return }
        let ratio = out.sampleRate / pcm.format.sampleRate
        let cap = AVAudioFrameCount(Double(pcm.frameLength) * ratio) + 16
        guard let dst = AVAudioPCMBuffer(pcmFormat: out, frameCapacity: cap) else { return }
        var fed = false
        var err: NSError?
        conv.convert(to: dst, error: &err) { _, st in
            if fed { st.pointee = .noDataNow; return nil }
            fed = true
            st.pointee = .haveData
            return pcm
        }
        if err == nil, dst.frameLength > 0 {
            cont.yield(AnalyzerInput(buffer: dst, bufferStartTime: start))
        }
    }

    private static func pcmBuffer(from sb: CMSampleBuffer) -> AVAudioPCMBuffer? {
        guard let desc = CMSampleBufferGetFormatDescription(sb) else { return nil }
        let format = AVAudioFormat(cmAudioFormatDescription: desc)
        let frames = AVAudioFrameCount(CMSampleBufferGetNumSamples(sb))
        guard frames > 0, let buf = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frames)
        else { return nil }
        buf.frameLength = frames
        let st = CMSampleBufferCopyPCMDataIntoAudioBufferList(
            sb, at: 0, frameCount: Int32(frames), into: buf.mutableAudioBufferList)
        return st == noErr ? buf : nil
    }
}

// MARK: - What's on screen and what's saved

/// The last `keep` seconds of finished sentences, plus the sentence still being spoken.
final class LiveText {
    let keep: TimeInterval = 30
    private var finals: [(at: Date, text: String)] = []
    private var partial = ""

    func add(_ c: Caption) {
        if c.isFinal {
            let t = c.text.trimmingCharacters(in: .whitespaces)
            if !t.isEmpty { finals.append((Date(), t)) }
            partial = ""
        } else {
            partial = c.text.trimmingCharacters(in: .whitespaces)
        }
    }

    /// Drops what's older than `keep`; returns true if anything was dropped.
    func prune() -> Bool {
        let cutoff = Date().addingTimeInterval(-keep)
        let before = finals.count
        finals.removeAll { $0.at < cutoff }
        return finals.count != before
    }

    var text: String { (finals.map(\.text) + (partial.isEmpty ? [] : [partial])).joined(separator: " ") }
}

/// One text file per session in ~/Documents/BubbleHead Transcripts, a line per
/// sentence with its time since the session started: "[01:23] Hello there."
final class TranscriptFile {
    static var folder: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("BubbleHead Transcripts")
    }

    private var handle: FileHandle?
    private var url: URL?
    private let startHost = CMClockGetTime(CMClockGetHostTimeClock())

    /// The file is created on the first sentence, so silent sessions leave nothing behind.
    func write(_ c: Caption) {
        let text = c.text.trimmingCharacters(in: .whitespaces)
        guard c.isFinal, !text.isEmpty else { return }
        if handle == nil {
            let f = DateFormatter()
            f.dateFormat = "yyyy-MM-dd HH-mm-ss"
            let url = Self.folder.appendingPathComponent("\(f.string(from: Date())).txt")
            try? FileManager.default.createDirectory(at: Self.folder, withIntermediateDirectories: true)
            FileManager.default.createFile(atPath: url.path, contents: nil)
            handle = try? FileHandle(forWritingTo: url)
            self.url = url
        }
        let secs = max(0, Int(CMTimeGetSeconds(CMTimeSubtract(c.start, startHost))))
        let line = String(format: "[%02d:%02d] ", secs / 60, secs % 60) + text + "\n"
        handle?.write(line.data(using: .utf8)!)
    }

    func close() {
        try? handle?.close()
        handle = nil
    }
}

// MARK: - The box under the bubble

final class TranscriptPanel: NSPanel {
    static let lines = 4
    let label = NSTextField(wrappingLabelWithString: "")
    private let font = NSFont.systemFont(ofSize: 15, weight: .medium)

    init() {
        super.init(contentRect: NSRect(x: 0, y: 0, width: 360, height: 100),
                   styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
        level = .screenSaver
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary, .ignoresCycle]
        hidesOnDeactivate = false
        isOpaque = false
        backgroundColor = .clear
        hasShadow = false
        ignoresMouseEvents = true   // clicks go through to whatever is underneath

        let box = NSView()
        box.wantsLayer = true
        box.layer?.backgroundColor = NSColor.black.withAlphaComponent(0.65).cgColor
        box.layer?.cornerRadius = 10
        label.font = font
        label.textColor = .white
        label.alignment = .left
        label.translatesAutoresizingMaskIntoConstraints = false
        box.addSubview(label)
        NSLayoutConstraint.activate([
            label.leadingAnchor.constraint(equalTo: box.leadingAnchor, constant: 12),
            label.trailingAnchor.constraint(equalTo: box.trailingAnchor, constant: -12),
            label.bottomAnchor.constraint(equalTo: box.bottomAnchor, constant: -8),
        ])
        contentView = box
    }

    /// Height that fits `lines` lines of text plus padding.
    static func height(for font: NSFont = .systemFont(ofSize: 15, weight: .medium)) -> CGFloat {
        ceil((font.ascender - font.descender + font.leading + 1) * CGFloat(lines)) + 16
    }

    /// Shows the newest words that fit; older lines scroll off the top.
    func show(_ text: String) {
        let width = frame.width - 24
        let attrs: [NSAttributedString.Key: Any] = [.font: font]
        func height(_ t: String) -> CGFloat {
            (t as NSString).boundingRect(with: NSSize(width: width, height: 10_000),
                                         options: .usesLineFragmentOrigin, attributes: attrs).height
        }
        var words = text.split(separator: " ").map(String.init)
        while words.count > 1, height(words.joined(separator: " ")) > frame.height - 14 {
            words.removeFirst()
        }
        label.stringValue = words.joined(separator: " ")
    }
}
