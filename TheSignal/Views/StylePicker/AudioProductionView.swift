import SwiftUI

struct AudioProductionView: View {
    @Binding var config: AudioProductionConfig

    var body: some View {
        VStack(spacing: 16) {
            silenceSlider
            fadeControls
            normalizeToggle
        }
    }

    private var silenceSlider: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Gap Between Segments")
                    .font(.caption)
                    .foregroundStyle(Color.textSecondary)
                Spacer()
                Text("\(config.silenceDurationMs)ms")
                    .font(.caption.monospaced())
                    .foregroundStyle(Color.textMuted)
            }
            Slider(
                value: Binding(
                    get: { Double(config.silenceDurationMs) },
                    set: { config.silenceDurationMs = Int($0) }
                ),
                in: 100...1000,
                step: 50
            )
            .tint(Color.accentBlue)

            Text("Shorter for rapid-fire, longer for dramatic pauses")
                .font(.caption2)
                .foregroundStyle(Color.textMuted.opacity(0.7))
        }
    }

    private var fadeControls: some View {
        HStack(spacing: 16) {
            fadeControl("Fade In", value: $config.fadeInMs)
            fadeControl("Fade Out", value: $config.fadeOutMs)
        }
    }

    private func fadeControl(_ label: String, value: Binding<Int>) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption)
                .foregroundStyle(Color.textSecondary)

            HStack {
                Button {
                    if value.wrappedValue > 0 {
                        value.wrappedValue -= 50
                    }
                } label: {
                    Image(systemName: "minus")
                        .font(.caption.weight(.semibold))
                        .frame(width: 28, height: 28)
                        .background(Color.surface, in: .circle)
                }
                .buttonStyle(.plain)
                .disabled(value.wrappedValue <= 0)

                Text("\(value.wrappedValue)ms")
                    .font(.caption.monospaced())
                    .frame(minWidth: 50)

                Button {
                    if value.wrappedValue < 500 {
                        value.wrappedValue += 50
                    }
                } label: {
                    Image(systemName: "plus")
                        .font(.caption.weight(.semibold))
                        .frame(width: 28, height: 28)
                        .background(Color.surface, in: .circle)
                }
                .buttonStyle(.plain)
                .disabled(value.wrappedValue >= 500)
            }
        }
        .frame(maxWidth: .infinity)
    }

    private var normalizeToggle: some View {
        Toggle(isOn: $config.normalize) {
            VStack(alignment: .leading, spacing: 2) {
                Text("Normalize Volume")
                    .font(.subheadline)
                    .foregroundStyle(Color.textPrimary)
                Text("Even out audio levels across segments")
                    .font(.caption2)
                    .foregroundStyle(Color.textMuted)
            }
        }
        .tint(Color.accentBlue)
    }
}
