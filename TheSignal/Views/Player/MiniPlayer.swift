import SwiftUI

struct MiniPlayer: View {
    @Environment(AudioManager.self) private var audio
    let onTap: () -> Void

    var body: some View {
        if audio.currentEpisode != nil {
            Button(action: onTap) {
                HStack(spacing: 12) {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.accentBlue.opacity(0.3))
                        .frame(width: 40, height: 40)
                        .overlay {
                            Image(systemName: "waveform")
                                .font(.caption)
                                .foregroundStyle(Color.accentBlue)
                                .symbolEffect(.variableColor.iterative, isActive: audio.isPlaying)
                        }

                    VStack(alignment: .leading, spacing: 2) {
                        Text("The Signal")
                            .font(.subheadline.weight(.medium))
                            .foregroundStyle(Color.textPrimary)
                            .lineLimit(1)

                        GeometryReader { geo in
                            let progress = audio.duration > 0 ? audio.currentTime / audio.duration : 0
                            ZStack(alignment: .leading) {
                                Capsule()
                                    .fill(Color.border)
                                    .frame(height: 3)
                                Capsule()
                                    .fill(Color.accentBlue)
                                    .frame(width: geo.size.width * progress, height: 3)
                            }
                        }
                        .frame(height: 3)
                    }

                    Spacer()

                    Button {
                        audio.toggle()
                    } label: {
                        Image(systemName: audio.isPlaying ? "pause.fill" : "play.fill")
                            .font(.title3)
                            .foregroundStyle(Color.textPrimary)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(.ultraThinMaterial)
            }
            .buttonStyle(.plain)
        }
    }
}
