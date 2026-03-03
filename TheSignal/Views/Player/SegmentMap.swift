import SwiftUI

struct SegmentMap: View {
    let segments: [ScriptSegment]
    let currentTime: TimeInterval
    let duration: TimeInterval
    let onSeek: (TimeInterval) -> Void

    var body: some View {
        GeometryReader { geo in
            let totalChars = segments.reduce(0) { $0 + $1.charCount }
            let width = geo.size.width

            ZStack(alignment: .leading) {
                HStack(spacing: 1) {
                    ForEach(Array(segments.enumerated()), id: \.offset) { index, segment in
                        let fraction = totalChars > 0 ? CGFloat(segment.charCount) / CGFloat(totalChars) : 0
                        let segWidth = max(2, fraction * width - 1)

                        RoundedRectangle(cornerRadius: 3)
                            .fill(segment.speakerColor.opacity(0.4))
                            .frame(width: segWidth)
                            .overlay(alignment: .leading) {
                                if segWidth > 30 {
                                    Text(segment.speaker)
                                        .font(.system(size: 7, weight: .bold, design: .monospaced))
                                        .foregroundStyle(segment.speakerColor)
                                        .padding(.leading, 3)
                                }
                            }
                            .onTapGesture {
                                let segmentStartFraction = segmentOffset(at: index, totalChars: totalChars)
                                let seekTime = segmentStartFraction * duration
                                onSeek(seekTime)
                            }
                    }
                }

                if duration > 0 {
                    let progress = min(currentTime / duration, 1.0)
                    Rectangle()
                        .fill(Color.textPrimary)
                        .frame(width: 2)
                        .offset(x: progress * width)
                }
            }
        }
    }

    private func segmentOffset(at index: Int, totalChars: Int) -> Double {
        guard totalChars > 0 else { return 0 }
        let preceding = segments.prefix(index).reduce(0) { $0 + $1.charCount }
        return Double(preceding) / Double(totalChars)
    }
}
