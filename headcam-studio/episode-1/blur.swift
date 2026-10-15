// Background blur and picture: Vision finds the person in each frame. Behind
// them, bottom to top: the room (blurred), then a crisp picture of your choice.
// The result is shown on a layer over the live preview.

import AppKit
import AVFoundation
import CoreImage
import Vision

enum Blur: String, CaseIterable {
    case off = "No Blur"
    case soft = "Soft Blur"
    case strong = "Strong Blur"

    /// Blur radius as a share of the bubble's width, so it looks the same at any size.
    var amount: CGFloat {
        switch self {
        case .off: return 0
        case .soft: return 0.02
        case .strong: return 0.05
        }
    }
}

/// Where the picture sits in the bubble: zoom (1 = just fills it) and how far its
/// center is moved, in bubble widths. It may spill past the rim (the bubble clips it)
/// or leave gaps (the blurred room shows there); limits only stop it getting lost.
struct PictureFraming: Equatable {
    var zoom: CGFloat = 1
    var x: CGFloat = 0
    var y: CGFloat = 0

    /// `aspect` is the picture's width / height.
    func clamped(aspect: CGFloat) -> PictureFraming {
        let z = min(max(zoom, 0.2), 8)
        // Keep at least a sliver of the picture inside the bubble.
        let mx = (z * max(1, aspect) + 1) / 2 - 0.05
        let my = (z * max(1, 1 / aspect) + 1) / 2 - 0.05
        return PictureFraming(zoom: z, x: min(max(x, -mx), mx), y: min(max(y, -my), my))
    }
}

final class BackgroundBlur: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    let output = AVCaptureVideoDataOutput()
    private let queue = DispatchQueue(label: "bubblehead.blur", qos: .userInteractive)
    private let request = VNGeneratePersonSegmentationRequest()
    private let sequence = VNSequenceRequestHandler()
    private let context = CIContext(options: [.cacheIntermediates: false])
    private let layer: CALayer

    // Read on the video queue, written on the main thread.
    private let lock = NSLock()
    private var _amount: CGFloat = 0
    private var _side: CGFloat = 440
    private var _mirror = true
    private var _picture: URL?
    private var _framing = PictureFraming()
    private var cacheKey = ""          // the prepared picture, so it isn't re-blurred every frame
    private var cachedPicture: CIImage?

    init(layer: CALayer) {
        self.layer = layer
        super.init()
        request.qualityLevel = .balanced
        request.outputPixelFormat = kCVPixelFormatType_OneComponent8
        output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
        output.alwaysDiscardsLateVideoFrames = true
        output.setSampleBufferDelegate(self, queue: queue)
    }

    /// Output size in pixels (the bubble's width on screen), blur strength, mirroring,
    /// and the picture to put behind the person instead of the room (nil for the room).
    func configure(blur: Blur, side: CGFloat, mirror: Bool, picture: URL?, framing: PictureFraming) {
        lock.lock()
        _amount = blur.amount
        _side = max(side, 64)
        _mirror = mirror
        _picture = picture
        _framing = framing
        lock.unlock()
    }

    /// The picture filling a side×side square (aspect fill, zoomed and moved by `f`,
    /// never mirrored, never blurred).
    private func preparedPicture(_ url: URL, side: CGFloat, framing f: PictureFraming) -> CIImage? {
        let key = "\(url.path)|\(Int(side))|\(f.zoom)|\(f.x)|\(f.y)"
        if key == cacheKey { return cachedPicture }
        cacheKey = key
        cachedPicture = nil
        guard let image = CIImage(contentsOf: url), !image.extent.isEmpty else { return nil }
        let e = image.extent
        let k = max(side / e.width, side / e.height) * f.zoom
        let out = CGRect(x: 0, y: 0, width: side, height: side)
        var bg = image.transformed(by: CGAffineTransform(translationX: -e.minX, y: -e.minY)
            .concatenating(CGAffineTransform(scaleX: k, y: k)))
        bg = bg.transformed(by: CGAffineTransform(translationX: (side - bg.extent.width) / 2 + f.x * side,
                                                  y: (side - bg.extent.height) / 2 + f.y * side))
            .cropped(to: out)
        guard let cg = context.createCGImage(bg, from: out) else { return nil }
        cachedPicture = CIImage(cgImage: cg)
        return cachedPicture
    }

    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer,
                       from connection: AVCaptureConnection) {
        lock.lock()
        let (amount, side, mirror, picture, framing) = (_amount, _side, _mirror, _picture, _framing)
        lock.unlock()
        guard amount > 0 || picture != nil, let pixels = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        guard (try? sequence.perform([request], on: pixels)) != nil,
              let maskPixels = request.results?.first?.pixelBuffer else { return }

        let frame = CIImage(cvPixelBuffer: pixels)
        let e = frame.extent
        var mask = CIImage(cvPixelBuffer: maskPixels)
        mask = mask.transformed(by: CGAffineTransform(scaleX: e.width / mask.extent.width,
                                                      y: e.height / mask.extent.height))

        // Center square of the frame, scaled to the bubble's pixel size (and mirrored).
        let s = min(e.width, e.height)
        let square = CGRect(x: e.midX - s / 2, y: e.midY - s / 2, width: s, height: s)
        let k = side / s
        var t = CGAffineTransform(translationX: -square.minX, y: -square.minY)
            .concatenating(CGAffineTransform(scaleX: k, y: k))
        if mirror {
            t = t.concatenating(CGAffineTransform(scaleX: -1, y: 1))
                 .concatenating(CGAffineTransform(translationX: side, y: 0))
        }
        let out = CGRect(x: 0, y: 0, width: side, height: side)
        let person = frame.cropped(to: square).transformed(by: t)
        let edge = mask.cropped(to: square).transformed(by: t)
            .applyingGaussianBlur(sigma: side * 0.006).cropped(to: out)   // soften the cut-out edge
        var room = amount > 0
            ? person.clampedToExtent().applyingGaussianBlur(sigma: side * amount).cropped(to: out)
            : person
        if let pic = picture.flatMap({ preparedPicture($0, side: side, framing: framing) }) {
            room = pic.composited(over: room)   // see-through parts of the picture show the room
        }
        let result = person.applyingFilter("CIBlendWithMask", parameters: [
            kCIInputBackgroundImageKey: room,
            kCIInputMaskImageKey: edge,
        ])
        guard let image = context.createCGImage(result, from: out) else { return }
        DispatchQueue.main.async {
            CATransaction.begin()
            CATransaction.setDisableActions(true)
            self.layer.contents = image
            CATransaction.commit()
        }
    }
}
