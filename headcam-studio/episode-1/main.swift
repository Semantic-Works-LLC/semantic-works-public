// BubbleHead: your webcam as a floating bubble above every app.
//
// Drag to move, scroll or pinch to resize, right-click for options.
// ⌃⌥B shows or hides the bubble from any app; ⌃⌥T turns the live transcript on or off.

import AppKit
import AVFoundation
import Carbon.HIToolbox
import UniformTypeIdentifiers

// MARK: - Settings

enum Shape: String, CaseIterable {
    case circle = "Circle"
    case rounded = "Rounded Square"
}

struct Settings {
    private static let d = UserDefaults.standard

    static var cameraID: String? {
        get { d.string(forKey: "cameraID") }
        set { d.set(newValue, forKey: "cameraID") }
    }
    static var mirror: Bool {
        get { d.object(forKey: "mirror") as? Bool ?? true }
        set { d.set(newValue, forKey: "mirror") }
    }
    static var shape: Shape {
        get { Shape(rawValue: d.string(forKey: "shape") ?? "") ?? .circle }
        set { d.set(newValue.rawValue, forKey: "shape") }
    }
    static var blur: Blur {
        get { Blur(rawValue: d.string(forKey: "blur") ?? "") ?? .off }
        set { d.set(newValue.rawValue, forKey: "blur") }
    }
    static var usePicture: Bool {
        get { d.bool(forKey: "usePicture") }
        set { d.set(newValue, forKey: "usePicture") }
    }
    /// The picture behind you, copied into Application Support so it survives the original moving.
    static var picture: URL? {
        get {
            // Your chosen picture, or the one that ships inside the app.
            guard let path = d.string(forKey: "picturePath"),
                  FileManager.default.fileExists(atPath: path) else {
                return Bundle.main.url(forResource: "background", withExtension: "png")
            }
            return URL(fileURLWithPath: path)
        }
        set { d.set(newValue?.path, forKey: "picturePath") }
    }
    static var framing: PictureFraming {
        get {
            guard let a = d.array(forKey: "pictureFraming") as? [Double], a.count == 3 else { return .init() }
            return PictureFraming(zoom: a[0], x: a[1], y: a[2])
        }
        set { d.set([Double(newValue.zoom), Double(newValue.x), Double(newValue.y)], forKey: "pictureFraming") }
    }
    static var transcript: Bool {
        get { d.bool(forKey: "transcript") }
        set { d.set(newValue, forKey: "transcript") }
    }
    static var ring: Bool {
        get { d.object(forKey: "ring") as? Bool ?? true }
        set { d.set(newValue, forKey: "ring") }
    }
    static var size: CGFloat {
        get { CGFloat(d.object(forKey: "size") as? Double ?? 220) }
        set { d.set(Double(newValue), forKey: "size") }
    }
    static var origin: NSPoint? {
        get {
            guard let a = d.array(forKey: "origin") as? [Double], a.count == 2 else { return nil }
            return NSPoint(x: a[0], y: a[1])
        }
        set { d.set(newValue.map { [Double($0.x), Double($0.y)] }, forKey: "origin") }
    }
}

// MARK: - Camera

final class Camera {
    let session = AVCaptureSession()
    private var input: AVCaptureDeviceInput?

    static func devices() -> [AVCaptureDevice] {
        var types: [AVCaptureDevice.DeviceType] = [.builtInWideAngleCamera, .continuityCamera]
        if #available(macOS 14.0, *) { types.append(.external) }
        return AVCaptureDevice.DiscoverySession(deviceTypes: types, mediaType: .video,
                                                position: .unspecified).devices
    }

    var current: AVCaptureDevice? { input?.device }

    /// Switches to the camera with this ID, or the system default if it's gone.
    func use(_ id: String?) {
        let device = id.flatMap { AVCaptureDevice(uniqueID: $0) }
            ?? AVCaptureDevice.default(for: .video)
            ?? Camera.devices().first
        guard let device, device != current else { return }
        session.beginConfiguration()
        if let input { session.removeInput(input) }
        if let newInput = try? AVCaptureDeviceInput(device: device), session.canAddInput(newInput) {
            session.addInput(newInput)
            input = newInput
        } else {
            input = nil
        }
        session.sessionPreset = session.canSetSessionPreset(.hd1280x720) ? .hd1280x720 : .high
        session.commitConfiguration()
    }

    func start() { DispatchQueue.global(qos: .userInitiated).async { self.session.startRunning() } }
    func stop() { DispatchQueue.global(qos: .userInitiated).async { self.session.stopRunning() } }
}

// MARK: - Bubble view

final class BubbleView: NSView {
    let preview: AVCaptureVideoPreviewLayer
    let blurred = CALayer()   // background-blurred frames, drawn over the preview
    private let ring = CAShapeLayer()
    private var dragStart: NSPoint?
    private var windowStart: NSPoint?
    var onResize: ((CGFloat, NSPoint) -> Void)?   // new size, anchor point in screen coordinates
    var onMoved: (() -> Void)?
    var menuProvider: (() -> NSMenu)?
    var onClick: (() -> Void)?
    /// Adjust mode: the arrow keys move the picture; shown with a yellow ring.
    var adjusting = false { didSet { needsLayout = true } }

    init(session: AVCaptureSession) {
        preview = AVCaptureVideoPreviewLayer(session: session)
        super.init(frame: .zero)
        wantsLayer = true
        layer = CALayer()
        layer!.masksToBounds = true
        preview.videoGravity = .resizeAspectFill
        layer!.addSublayer(preview)
        blurred.contentsGravity = .resizeAspectFill
        blurred.isHidden = true
        layer!.addSublayer(blurred)
        ring.fillColor = nil
        ring.lineWidth = 3
        layer!.addSublayer(ring)
    }
    required init?(coder: NSCoder) { fatalError() }

    override func layout() {
        super.layout()
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        let b = bounds
        let radius = Settings.shape == .circle ? b.width / 2 : b.width * 0.22
        layer?.cornerRadius = radius
        preview.frame = b
        blurred.frame = b
        let inset = ring.lineWidth / 2
        ring.path = CGPath(roundedRect: b.insetBy(dx: inset, dy: inset),
                           cornerWidth: radius - inset, cornerHeight: radius - inset, transform: nil)
        ring.isHidden = !Settings.ring && !adjusting
        ring.strokeColor = adjusting ? NSColor.systemYellow.cgColor
                                     : NSColor.white.withAlphaComponent(0.9).cgColor
        if let scale = window?.backingScaleFactor {
            preview.contentsScale = scale
            blurred.contentsScale = scale
            ring.contentsScale = scale
        }
        CATransaction.commit()
    }

    func applyMirror() {
        guard let c = preview.connection, c.isVideoMirroringSupported else { return }
        c.automaticallyAdjustsVideoMirroring = false
        c.isVideoMirrored = Settings.mirror
    }

    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }

    // Moving: track the mouse in screen coordinates so the bubble never jitters.
    override func mouseDown(with event: NSEvent) {
        onClick?()
        dragStart = NSEvent.mouseLocation
        windowStart = window?.frame.origin
    }
    override func mouseDragged(with event: NSEvent) {
        guard let dragStart, let windowStart, let window else { return }
        let now = NSEvent.mouseLocation
        window.setFrameOrigin(NSPoint(x: windowStart.x + now.x - dragStart.x,
                                      y: windowStart.y + now.y - dragStart.y))
    }
    override func mouseUp(with event: NSEvent) {
        if dragStart != nil { onMoved?() }
        dragStart = nil
    }

    // Resizing: scroll wheel or trackpad pinch, around the pointer's spot.
    override func scrollWheel(with event: NSEvent) {
        let delta = event.hasPreciseScrollingDeltas ? event.scrollingDeltaY : event.scrollingDeltaY * 8
        onResize?(bounds.width + delta, NSEvent.mouseLocation)
    }
    override func magnify(with event: NSEvent) {
        onResize?(bounds.width * (1 + event.magnification), NSEvent.mouseLocation)
    }

    override func menu(for event: NSEvent) -> NSMenu? { menuProvider?() }
}

// MARK: - Bubble window

final class BubbleWindow: NSPanel {
    init(view: BubbleView) {
        super.init(contentRect: NSRect(x: 0, y: 0, width: 220, height: 220),
                   styleMask: [.borderless, .nonactivatingPanel],
                   backing: .buffered, defer: false)
        isOpaque = false
        backgroundColor = .clear
        hasShadow = true
        // Above regular windows, full-screen apps and the Dock, on every Space.
        level = .screenSaver
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary, .ignoresCycle]
        hidesOnDeactivate = false
        isMovable = false   // BubbleView moves it, so clicks never start a system drag
        contentView = view
    }
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }
}

// MARK: - App

final class AppDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate {
    static let minSize: CGFloat = 80
    static let maxSize: CGFloat = 900

    let camera = Camera()
    var view: BubbleView!
    var blur: BackgroundBlur!
    var window: BubbleWindow!
    var statusItem: NSStatusItem!
    var hotKey: EventHotKeyRef?
    var transcriptHotKey: EventHotKeyRef?

    // Live transcript
    let mic = Microphone()
    var captioner: AnyObject?          // Captioner, which needs macOS 26
    let liveText = LiveText()
    var transcriptFile: TranscriptFile?
    let transcriptPanel = TranscriptPanel()
    var pruneTimer: Timer?
    var transcriptStatus = ""

    func applicationDidFinishLaunching(_ note: Notification) {
        view = BubbleView(session: camera.session)
        window = BubbleWindow(view: view)
        blur = BackgroundBlur(layer: view.blurred)
        view.onResize = { [weak self] size, anchor in self?.resize(to: size, around: anchor) }
        view.onMoved = { [weak self] in self?.saveFrame(); self?.placeTranscriptPanel() }
        view.menuProvider = { [weak self] in self?.makeMenu() ?? NSMenu() }
        view.onClick = { [weak self] in self?.startAdjusting() }

        placeWindow()
        setUpStatusItem()
        registerHotKey()

        let nc = NotificationCenter.default
        nc.addObserver(self, selector: #selector(camerasChanged),
                       name: AVCaptureDevice.wasConnectedNotification, object: nil)
        nc.addObserver(self, selector: #selector(camerasChanged),
                       name: AVCaptureDevice.wasDisconnectedNotification, object: nil)
        nc.addObserver(self, selector: #selector(screensChanged),
                       name: NSApplication.didChangeScreenParametersNotification, object: nil)

        AVCaptureDevice.requestAccess(for: .video) { granted in
            DispatchQueue.main.async {
                guard granted else { return self.explainNoAccess() }
                self.camera.use(Settings.cameraID)
                self.view.applyMirror()
                self.applyBlur()
                self.camera.start()
                self.window.orderFrontRegardless()
                if Settings.transcript { self.startTranscript() }
            }
        }
    }

    func applicationWillTerminate(_ note: Notification) {
        camera.session.stopRunning()
        transcriptFile?.close()
    }

    // MARK: Placement

    func placeWindow() {
        let size = Settings.size
        var origin = Settings.origin ?? {
            let v = NSScreen.main?.visibleFrame ?? NSRect(x: 0, y: 0, width: 1440, height: 900)
            return NSPoint(x: v.maxX - size - 40, y: v.minY + 40)   // bottom right
        }()
        let frame = NSRect(origin: origin, size: NSSize(width: size, height: size))
        if !NSScreen.screens.contains(where: { $0.frame.intersects(frame) }) {
            let v = NSScreen.main?.visibleFrame ?? .zero
            origin = NSPoint(x: v.maxX - size - 40, y: v.minY + 40)
        }
        window.setFrame(NSRect(origin: origin, size: NSSize(width: size, height: size)), display: true)
        placeTranscriptPanel()
    }

    func resize(to newSize: CGFloat, around anchor: NSPoint) {
        let size = min(max(newSize, Self.minSize), Self.maxSize).rounded()
        let f = window.frame
        guard size != f.width else { return }
        // Keep the spot under the pointer (or the center) where it is.
        let ax = f.width > 0 ? (anchor.x - f.minX) / f.width : 0.5
        let ay = f.height > 0 ? (anchor.y - f.minY) / f.height : 0.5
        let fx = min(max(ax, 0), 1), fy = min(max(ay, 0), 1)
        let origin = NSPoint(x: f.minX + (f.width - size) * fx, y: f.minY + (f.height - size) * fy)
        window.setFrame(NSRect(origin: origin, size: NSSize(width: size, height: size)), display: true)
        window.invalidateShadow()
        saveFrame()
        updateBlur()
        placeTranscriptPanel()
    }

    /// Adds the blur's video output to the session only while blur is on, to save power.
    func applyBlur() {
        let on = Settings.blur != .off || activePicture != nil
        let s = camera.session
        let attached = s.outputs.contains(blur.output)
        updateBlur()
        if on && !attached {
            s.beginConfiguration()
            if s.canAddOutput(blur.output) { s.addOutput(blur.output) }
            s.commitConfiguration()
        } else if !on && attached {
            s.beginConfiguration()
            s.removeOutput(blur.output)
            s.commitConfiguration()
        }
        if !on { view.blurred.contents = nil }
        view.blurred.isHidden = !on
    }

    func updateBlur() {
        blur.configure(blur: Settings.blur,
                       side: window.frame.width * window.backingScaleFactor,
                       mirror: Settings.mirror, picture: activePicture, framing: Settings.framing)
    }

    // MARK: Moving the picture with the keyboard
    //
    // The bubble never takes keyboard focus from the app you're presenting, so
    // clicking it enters an adjust mode that briefly claims these keys as hot keys
    // (no Accessibility permission needed). Clicking anywhere else, Esc or Return ends it.

    enum PictureKey: UInt32 {
        case left = 10, right, up, down, bigLeft, bigRight, bigUp, bigDown
        case zoomIn, zoomInShift, zoomInPad, zoomOut, zoomOutPad, reset, done, doneReturn
    }
    static let pictureKeys: [(PictureKey, Int, Int)] = [
        (.left, kVK_LeftArrow, 0), (.right, kVK_RightArrow, 0),
        (.up, kVK_UpArrow, 0), (.down, kVK_DownArrow, 0),
        (.bigLeft, kVK_LeftArrow, shiftKey), (.bigRight, kVK_RightArrow, shiftKey),
        (.bigUp, kVK_UpArrow, shiftKey), (.bigDown, kVK_DownArrow, shiftKey),
        (.zoomIn, kVK_ANSI_Equal, 0), (.zoomInShift, kVK_ANSI_Equal, shiftKey),
        (.zoomInPad, kVK_ANSI_KeypadPlus, 0), (.zoomOut, kVK_ANSI_Minus, 0),
        (.zoomOutPad, kVK_ANSI_KeypadMinus, 0), (.reset, kVK_ANSI_0, 0),
        (.done, kVK_Escape, 0), (.doneReturn, kVK_Return, 0),
    ]
    var adjustKeys: [EventHotKeyRef] = []
    var outsideClicks: Any?
    var repeatTimer: Timer?

    func startAdjusting() {
        guard activePicture != nil, adjustKeys.isEmpty else { return }
        for (key, code, mods) in Self.pictureKeys {
            var ref: EventHotKeyRef?
            let id = EventHotKeyID(signature: OSType(0x4248_4344), id: key.rawValue)
            if RegisterEventHotKey(UInt32(code), UInt32(mods), id, GetApplicationEventTarget(), 0, &ref) == noErr,
               let ref { adjustKeys.append(ref) }
        }
        // Global monitors only see clicks in other apps, which is exactly "clicked elsewhere".
        outsideClicks = NSEvent.addGlobalMonitorForEvents(matching: [.leftMouseDown, .rightMouseDown]) {
            [weak self] _ in self?.stopAdjusting()
        }
        view.adjusting = true
    }

    func stopAdjusting() {
        adjustKeys.forEach { UnregisterEventHotKey($0) }
        adjustKeys = []
        if let outsideClicks { NSEvent.removeMonitor(outsideClicks) }
        outsideClicks = nil
        repeatTimer?.invalidate()
        view.adjusting = false
    }

    func hotKey(_ id: UInt32, pressed: Bool) {
        if id == 1 { if pressed { toggleVisible() }; return }
        if id == 2 { if pressed { toggleTranscript() }; return }
        guard let key = PictureKey(rawValue: id) else { return }
        repeatTimer?.invalidate()
        guard pressed else { return }
        movePicture(key)
        // Held keys keep moving (hot keys don't auto-repeat on their own).
        guard key.rawValue <= PictureKey.bigDown.rawValue else { return }
        repeatTimer = Timer.scheduledTimer(withTimeInterval: 0.35, repeats: false) { [weak self] _ in
            self?.repeatTimer = Timer.scheduledTimer(withTimeInterval: 0.04, repeats: true) { _ in
                self?.movePicture(key)
            }
        }
    }

    /// Arrows move the picture (⇧ for bigger steps), + and − zoom it, 0 resets.
    func movePicture(_ key: PictureKey) {
        guard let url = activePicture else { return stopAdjusting() }
        var f = Settings.framing
        switch key {
        case .left: f.x -= 0.02
        case .right: f.x += 0.02
        case .up: f.y += 0.02
        case .down: f.y -= 0.02
        case .bigLeft: f.x -= 0.1
        case .bigRight: f.x += 0.1
        case .bigUp: f.y += 0.1
        case .bigDown: f.y -= 0.1
        case .zoomIn, .zoomInShift, .zoomInPad: f.zoom *= 1.1
        case .zoomOut, .zoomOutPad: f.zoom /= 1.1
        case .reset: f = PictureFraming()
        case .done, .doneReturn: return stopAdjusting()
        }
        Settings.framing = f.clamped(aspect: pictureAspect(url))
        updateBlur()
    }

    private var aspectCache: (URL, CGFloat)?
    func pictureAspect(_ url: URL) -> CGFloat {
        if let (u, a) = aspectCache, u == url { return a }
        let e = CIImage(contentsOf: url)?.extent ?? CGRect(x: 0, y: 0, width: 1, height: 1)
        let a = e.height > 0 ? e.width / e.height : 1
        aspectCache = (url, a)
        return a
    }

    var activePicture: URL? { Settings.usePicture ? Settings.picture : nil }

    func saveFrame() {
        Settings.origin = window.frame.origin
        Settings.size = window.frame.width
    }

    @objc func screensChanged() { placeWindow() }

    // MARK: Menus

    func setUpStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        statusItem.button?.image = NSImage(systemSymbolName: "person.crop.circle",
                                           accessibilityDescription: "BubbleHead")
        let menu = NSMenu()
        menu.delegate = self   // rebuilt every time it opens, so the camera list is fresh
        statusItem.menu = menu
    }

    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.removeAllItems()
        for item in makeMenu().items {
            item.menu?.removeItem(item)
            menu.addItem(item)
        }
    }

    func makeMenu() -> NSMenu {
        let menu = NSMenu()
        let visible = window.isVisible
        menu.addItem(item(visible ? "Hide Bubble" : "Show Bubble", #selector(toggleVisible), key: "b",
                          modifiers: [.control, .option]))
        menu.addItem(.separator())

        menu.addItem(NSMenuItem.sectionHeader(title: "Camera"))
        let devices = Camera.devices()
        if devices.isEmpty {
            let none = NSMenuItem(title: "No camera found", action: nil, keyEquivalent: "")
            none.isEnabled = false
            menu.addItem(none)
        }
        for device in devices {
            let i = item(device.localizedName, #selector(pickCamera(_:)))
            i.representedObject = device.uniqueID
            i.state = device == camera.current ? .on : .off
            menu.addItem(i)
        }
        menu.addItem(.separator())

        menu.addItem(NSMenuItem.sectionHeader(title: "Look"))
        for shape in Shape.allCases {
            let i = item(shape.rawValue, #selector(pickShape(_:)))
            i.representedObject = shape.rawValue
            i.state = Settings.shape == shape ? .on : .off
            menu.addItem(i)
        }
        let mirror = item("Mirror", #selector(toggleMirror))
        mirror.state = Settings.mirror ? .on : .off
        menu.addItem(mirror)
        menu.addItem(.separator())

        menu.addItem(NSMenuItem.sectionHeader(title: "Background"))
        for b in Blur.allCases {
            let i = item(b.rawValue, #selector(pickBlur(_:)))
            i.representedObject = b.rawValue
            i.state = Settings.blur == b ? .on : .off
            menu.addItem(i)
        }
        let picture = item("Picture Behind Me", #selector(togglePicture))
        picture.state = activePicture != nil ? .on : .off
        picture.isEnabled = Settings.picture != nil
        menu.addItem(picture)
        menu.addItem(item("Choose Picture…", #selector(choosePicture)))
        if activePicture != nil {
            let hint = NSMenuItem(title: "Click bubble (yellow ring): ←↑→↓ move · + − zoom · 0 reset · Esc done",
                                  action: nil, keyEquivalent: "")
            hint.isEnabled = false
            menu.addItem(hint)
        }
        if #available(macOS 12.0, *) {
            menu.addItem(item("Apple Video Effects…", #selector(showVideoEffects)))
        }
        menu.addItem(.separator())

        menu.addItem(NSMenuItem.sectionHeader(title: "Transcript"))
        let live = item("Live Transcript", #selector(toggleTranscript), key: "t", modifiers: [.control, .option])
        live.state = Settings.transcript ? .on : .off
        menu.addItem(live)
        menu.addItem(item("Show Saved Transcripts", #selector(showTranscripts)))
        menu.addItem(.separator())

        let ring = item("White Ring", #selector(toggleRing))
        ring.state = Settings.ring ? .on : .off
        menu.addItem(ring)
        menu.addItem(.separator())

        menu.addItem(NSMenuItem.sectionHeader(title: "Size"))
        for (name, size) in [("Small", 140.0), ("Medium", 220.0), ("Large", 340.0), ("Huge", 520.0)] {
            let i = item(name, #selector(pickSize(_:)))
            i.representedObject = size
            i.state = abs(window.frame.width - size) < 1 ? .on : .off
            menu.addItem(i)
        }
        menu.addItem(.separator())
        menu.addItem(item("Reset Position", #selector(resetPosition)))
        menu.addItem(item("Quit BubbleHead", #selector(NSApplication.terminate(_:)), key: "q"))
        return menu
    }

    func item(_ title: String, _ action: Selector, key: String = "",
              modifiers: NSEvent.ModifierFlags = .command) -> NSMenuItem {
        let i = NSMenuItem(title: title, action: action, keyEquivalent: key)
        i.keyEquivalentModifierMask = modifiers
        i.target = action == #selector(NSApplication.terminate(_:)) ? NSApp : self
        return i
    }

    @objc func toggleVisible() {
        if window.isVisible {
            stopAdjusting()
            hideTranscriptPanel()
            window.orderOut(nil)
            camera.stop()   // camera light goes off while hidden
        } else {
            camera.start()
            window.orderFrontRegardless()
            if Settings.transcript { showTranscriptPanel() }
        }
    }

    @objc func pickCamera(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? String else { return }
        Settings.cameraID = id
        camera.use(id)
        view.applyMirror()
    }

    @objc func pickShape(_ sender: NSMenuItem) {
        guard let raw = sender.representedObject as? String, let shape = Shape(rawValue: raw) else { return }
        Settings.shape = shape
        view.needsLayout = true
        window.invalidateShadow()
    }

    @objc func toggleMirror() {
        Settings.mirror.toggle()
        view.applyMirror()
        updateBlur()
    }

    @objc func pickBlur(_ sender: NSMenuItem) {
        guard let raw = sender.representedObject as? String, let b = Blur(rawValue: raw) else { return }
        Settings.blur = b
        applyBlur()
    }

    @objc func togglePicture() {
        Settings.usePicture.toggle()
        stopAdjusting()
        applyBlur()
    }

    @objc func choosePicture() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.image]
        panel.message = "Choose a picture to show behind you"
        NSApp.activate(ignoringOtherApps: true)
        guard panel.runModal() == .OK, let source = panel.url else { return }
        let fm = FileManager.default
        guard let support = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first else { return }
        let dir = support.appendingPathComponent("BubbleHead")
        // A new name each time, so the cached blurred copy is never stale.
        let dest = dir.appendingPathComponent("background-\(Int(Date().timeIntervalSince1970)).\(source.pathExtension)")
        do {
            try fm.createDirectory(at: dir, withIntermediateDirectories: true)
            if let old = Settings.picture, old.path.hasPrefix(dir.path) { try? fm.removeItem(at: old) }
            try fm.copyItem(at: source, to: dest)
        } catch {
            NSAlert(error: error).runModal()
            return
        }
        Settings.picture = dest
        Settings.usePicture = true
        Settings.framing = PictureFraming()
        applyBlur()
    }

    /// macOS's own Portrait, Studio Light and other effects, set per app in Control Center.
    @available(macOS 12.0, *)
    @objc func showVideoEffects() {
        AVCaptureDevice.showSystemUserInterface(.videoEffects)
    }

    @objc func toggleRing() {
        Settings.ring.toggle()
        view.needsLayout = true
    }

    @objc func pickSize(_ sender: NSMenuItem) {
        guard let size = sender.representedObject as? Double else { return }
        let f = window.frame
        resize(to: size, around: NSPoint(x: f.midX, y: f.midY))
    }

    @objc func resetPosition() {
        Settings.origin = nil
        placeWindow()
    }

    @objc func camerasChanged() {
        // If the chosen camera came back, switch to it; if the current one left, fall back.
        if let id = Settings.cameraID, camera.current?.uniqueID != id,
           AVCaptureDevice(uniqueID: id) != nil {
            camera.use(id)
        } else if let current = camera.current, !current.isConnected {
            camera.use(nil)
        }
        view.applyMirror()
    }

    func explainNoAccess() {
        let alert = NSAlert()
        alert.messageText = "BubbleHead needs the camera"
        alert.informativeText = "Allow it in System Settings › Privacy & Security › Camera, then open BubbleHead again."
        alert.addButton(withTitle: "Open Settings")
        alert.addButton(withTitle: "Quit")
        NSApp.activate(ignoringOtherApps: true)
        if alert.runModal() == .alertFirstButtonReturn,
           let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera") {
            NSWorkspace.shared.open(url)
        }
        NSApp.terminate(nil)
    }

    // MARK: Live transcript

    @objc func toggleTranscript() {
        Settings.transcript.toggle()
        Settings.transcript ? startTranscript() : stopTranscript()
    }

    func startTranscript() {
        guard #available(macOS 26, *) else {
            Settings.transcript = false
            return alert("Live transcript needs macOS 26 or later.")
        }
        AVCaptureDevice.requestAccess(for: .audio) { granted in
            DispatchQueue.main.async {
                guard granted else {
                    Settings.transcript = false
                    return self.alert("BubbleHead needs the microphone for the live transcript. "
                        + "Allow it in System Settings › Privacy & Security › Microphone.")
                }
                guard Settings.transcript else { return }
                let c = (self.captioner as? Captioner) ?? Captioner()
                self.captioner = c
                // The app delegate lives as long as the app, so strong captures are fine here.
                c.onCaption = { cap in
                    self.liveText.add(cap)
                    self.transcriptFile?.write(cap)
                    self.refreshTranscript()
                }
                c.onStatus = { s in
                    self.transcriptStatus = s
                    self.refreshTranscript()
                }
                c.start()
                c.setPaused(false)
                self.mic.onBuffer = { [weak c] in c?.append($0) }
                self.mic.start()
                self.transcriptFile = TranscriptFile()
                self.pruneTimer?.invalidate()
                self.pruneTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { _ in
                    if self.liveText.prune() { self.refreshTranscript() }
                }
                if self.window.isVisible { self.showTranscriptPanel() }
                self.refreshTranscript()
            }
        }
    }

    func stopTranscript() {
        mic.stop()
        if #available(macOS 26, *) { (captioner as? Captioner)?.setPaused(true) }
        pruneTimer?.invalidate()
        hideTranscriptPanel()
        // The last sentence is finalized just after the pause, so close the file a moment later.
        let file = transcriptFile
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
            file?.close()
            if self.transcriptFile === file { self.transcriptFile = nil }
        }
    }

    func refreshTranscript() {
        let text = liveText.text
        transcriptPanel.label.textColor = text.isEmpty ? NSColor(white: 1, alpha: 0.5) : .white
        transcriptPanel.show(!transcriptStatus.isEmpty ? transcriptStatus : text.isEmpty ? "Listening…" : text)
    }

    func showTranscriptPanel() {
        placeTranscriptPanel()
        window.addChildWindow(transcriptPanel, ordered: .above)   // moves with the bubble
        transcriptPanel.orderFrontRegardless()
    }

    func hideTranscriptPanel() {
        window.removeChildWindow(transcriptPanel)
        transcriptPanel.orderOut(nil)
    }

    /// Under the bubble, or above it when there's no room below.
    func placeTranscriptPanel() {
        let b = window.frame
        let w = min(max(b.width * 1.3, 340), 640)
        let h = TranscriptPanel.height()
        var y = b.minY - 8 - h
        let screen = NSScreen.screens.first { $0.frame.intersects(b) } ?? NSScreen.main
        if let v = screen?.visibleFrame, y < v.minY { y = b.maxY + 8 }
        transcriptPanel.setFrame(NSRect(x: b.midX - w / 2, y: y, width: w, height: h), display: true)
        refreshTranscript()
    }

    @objc func showTranscripts() {
        try? FileManager.default.createDirectory(at: TranscriptFile.folder, withIntermediateDirectories: true)
        NSWorkspace.shared.open(TranscriptFile.folder)
    }

    func alert(_ text: String) {
        let a = NSAlert()
        a.messageText = text
        NSApp.activate(ignoringOtherApps: true)
        a.runModal()
    }

    // MARK: Global hot keys (⌃⌥B, ⌃⌥T), no Accessibility permission needed

    func registerHotKey() {
        var specs = [EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed)),
                     EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyReleased))]
        InstallEventHandler(GetApplicationEventTarget(), { _, event, ctx in
            let me = Unmanaged<AppDelegate>.fromOpaque(ctx!).takeUnretainedValue()
            var id = EventHotKeyID()
            GetEventParameter(event, EventParamName(kEventParamDirectObject), EventParamType(typeEventHotKeyID),
                              nil, MemoryLayout<EventHotKeyID>.size, nil, &id)
            let pressed = GetEventKind(event) == UInt32(kEventHotKeyPressed)
            DispatchQueue.main.async { me.hotKey(id.id, pressed: pressed) }
            return noErr
        }, 2, &specs, Unmanaged.passUnretained(self).toOpaque(), nil)
        let id = EventHotKeyID(signature: OSType(0x4248_4344), id: 1)   // 'BHCD'
        RegisterEventHotKey(UInt32(kVK_ANSI_B), UInt32(controlKey | optionKey), id,
                            GetApplicationEventTarget(), 0, &hotKey)
        let tid = EventHotKeyID(signature: OSType(0x4248_4344), id: 2)
        RegisterEventHotKey(UInt32(kVK_ANSI_T), UInt32(controlKey | optionKey), tid,
                            GetApplicationEventTarget(), 0, &transcriptHotKey)
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.accessory)
app.run()
