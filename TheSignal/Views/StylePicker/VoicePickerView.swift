import SwiftUI

struct VoicePickerView: View {
    let tone: Tone
    @Binding var voiceConfig: [String: SpeakerConfig]
    let availableVoices: [VoiceInfo]

    private var speakers: [String] {
        switch tone {
        case .casual: ["ALEX", "JAMIE"]
        case .polished: ["ANCHOR", "ANALYST"]
        case .debate: ["BULL", "BEAR"]
        case .technical: ["LEAD", "PEER"]
        }
    }

    var body: some View {
        VStack(spacing: 16) {
            ForEach(speakers, id: \.self) { speaker in
                SpeakerVoiceRow(
                    speaker: speaker,
                    config: binding(for: speaker),
                    voices: availableVoices
                )
            }
        }
    }

    private func binding(for speaker: String) -> Binding<SpeakerConfig> {
        Binding(
            get: { voiceConfig[speaker] ?? SpeakerConfig(voiceId: "") },
            set: { voiceConfig[speaker] = $0 }
        )
    }
}

struct SpeakerVoiceRow: View {
    let speaker: String
    @Binding var config: SpeakerConfig
    let voices: [VoiceInfo]
    @State private var showSettings = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(speaker)
                    .font(.caption.weight(.bold))
                    .foregroundStyle(speakerColor)
                Spacer()
                Button {
                    withAnimation(.snappy(duration: 0.2)) {
                        showSettings.toggle()
                    }
                } label: {
                    Image(systemName: "slider.horizontal.3")
                        .font(.caption)
                        .foregroundStyle(showSettings ? Color.accentBlue : Color.textMuted)
                }
            }

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(voices) { voice in
                        voicePill(voice)
                    }
                }
            }

            if showSettings {
                VStack(spacing: 12) {
                    settingSlider("Stability", value: $config.settings.stability,
                                  description: "Higher = more consistent")
                    settingSlider("Clarity", value: $config.settings.similarityBoost,
                                  description: "Higher = clearer voice")
                    settingSlider("Style", value: $config.settings.style,
                                  description: "Higher = more expressive")
                }
                .padding(.top, 8)
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
    }

    private var speakerColor: Color {
        switch speaker {
        case "ALEX", "ANCHOR", "HOST": .blue
        case "JAMIE": .orange
        case "ANALYST": .teal
        case "BULL": .green
        case "BEAR": .red
        case "LEAD": .purple
        case "PEER": .orange
        default: .gray
        }
    }

    private func voicePill(_ voice: VoiceInfo) -> some View {
        let isSelected = config.voiceId == voice.id
        return Button {
            withAnimation(.snappy(duration: 0.2)) {
                config.voiceId = voice.id
            }
        } label: {
            Text(voice.name.capitalized)
                .font(.caption.weight(.medium))
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(isSelected ? Color.accentBlue.opacity(0.2) : Color.clear, in: .capsule)
                .overlay(Capsule().strokeBorder(isSelected ? Color.accentBlue : Color.border))
                .foregroundStyle(isSelected ? Color.accentBlue : Color.textSecondary)
        }
        .buttonStyle(.plain)
    }

    private func settingSlider(_ label: String, value: Binding<Double>, description: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(label)
                    .font(.caption2)
                    .foregroundStyle(Color.textMuted)
                Spacer()
                Text(String(format: "%.0f%%", value.wrappedValue * 100))
                    .font(.caption2.monospaced())
                    .foregroundStyle(Color.textSecondary)
            }
            Slider(value: value, in: 0...1)
                .tint(Color.accentBlue)
            Text(description)
                .font(.caption2)
                .foregroundStyle(Color.textMuted.opacity(0.7))
        }
    }
}
