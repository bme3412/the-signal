import SwiftUI

struct EpisodeRow: View {
    let episode: Episode
    let onTap: () -> Void
    let onPlay: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                statusIcon
                    .frame(width: 40, height: 40)

                VStack(alignment: .leading, spacing: 4) {
                    Text(episode.displayTitle)
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(Color.textPrimary)
                        .lineLimit(2)

                    HStack(spacing: 6) {
                        Label(episode.status.displayName, systemImage: episode.status.icon)
                            .font(.caption)
                            .foregroundStyle(episode.status.color)

                        if let dur = episode.audioDuration {
                            Text("·")
                                .foregroundStyle(Color.textMuted)
                            Text("\(Int(dur / 60)) min")
                                .font(.caption.monospaced())
                                .foregroundStyle(Color.textMuted)
                        }

                        if let cost = episode.metrics?.estimatedCostUsd {
                            Text("·")
                                .foregroundStyle(Color.textMuted)
                            Text(String(format: "$%.2f", cost))
                                .font(.caption.monospaced())
                                .foregroundStyle(Color.textMuted)
                        }
                    }

                    Text(episode.createdAt, style: .relative)
                        .font(.caption2)
                        .foregroundStyle(Color.textMuted)
                }

                Spacer()

                if episode.status == .ready {
                    Button(action: onPlay) {
                        Image(systemName: "play.circle.fill")
                            .font(.title2)
                            .foregroundStyle(Color.accentBlue)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(.plain)
    }

    private var statusIcon: some View {
        RoundedRectangle(cornerRadius: 8)
            .fill(episode.status.color.opacity(0.15))
            .overlay {
                Image(systemName: episode.status.icon)
                    .font(.body)
                    .foregroundStyle(episode.status.color)
            }
    }
}
