import SwiftUI

struct StyleSummaryBar: View {
    let style: StyleConfig

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                summaryPill(style.depth.icon, style.depth.displayName, style.depth.color)
                summaryPill(style.tone.icon, style.tone.displayName, style.tone.color)
                summaryPill(style.lens.icon, style.lens.displayName, style.lens.color)
                summaryPill(style.pacing.icon, style.pacing.displayName, style.pacing.color)
                summaryPill(style.humor.icon, style.humor.displayName, style.humor.color)
                summaryPill(style.audience.icon, style.audience.displayName, style.audience.color)
                summaryPill(style.structure.icon, style.structure.displayName, style.structure.color)
                summaryPill(style.closer.icon, style.closer.displayName, style.closer.color)
            }
        }
    }

    private func summaryPill(_ icon: String, _ label: String, _ color: Color) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 9))
            Text(label)
                .font(.system(size: 10, weight: .medium, design: .monospaced))
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.12), in: .capsule)
        .foregroundStyle(color)
    }
}
