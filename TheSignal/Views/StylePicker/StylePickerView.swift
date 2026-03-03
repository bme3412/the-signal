import SwiftUI

struct StylePickerView: View {
    @Binding var style: StyleConfig
    @Binding var targetMinutes: Int
    @Binding var voiceConfig: [String: SpeakerConfig]
    @Binding var audioConfig: AudioProductionConfig

    @State private var expandedSections: Set<String> = ["Core Voice", "Delivery", "Structure"]
    @State private var availableVoices: [VoiceInfo] = []

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                StyleSummaryBar(style: style)
                    .padding(.horizontal)

                PresetCards(style: $style)
                    .padding(.horizontal)

                durationSlider
                    .padding(.horizontal)

                dimensionSections

                voiceSection

                audioSection
            }
            .padding(.vertical)
        }
        .task {
            await loadVoices()
        }
    }

    private var durationSlider: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Target Duration")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                Text("\(targetMinutes) min")
                    .font(.subheadline.monospaced().weight(.medium))
                    .foregroundStyle(Color.accentBlue)
            }

            Slider(value: Binding(
                get: { Double(targetMinutes) },
                set: { targetMinutes = Int($0) }
            ), in: 5...60, step: 5)
            .tint(Color.accentBlue)
        }
        .padding()
        .background(Color.surface, in: .rect(cornerRadius: 12))
    }

    private var dimensionSections: some View {
        VStack(spacing: 12) {
            collapsibleSection("Core Voice") {
                DimensionRow(title: "Depth", selection: $style.depth)
                DimensionRow(title: "Tone", selection: $style.tone)
                DimensionRow(title: "Lens", selection: $style.lens)
            }

            collapsibleSection("Delivery") {
                DimensionRow(title: "Pacing", selection: $style.pacing)
                DimensionRow(title: "Humor", selection: $style.humor)
                DimensionRow(title: "Audience", selection: $style.audience)
            }

            collapsibleSection("Structure") {
                DimensionRow(title: "Structure", selection: $style.structure)
                DimensionRow(title: "Closer", selection: $style.closer)
            }
        }
        .padding(.horizontal)
    }

    private var voiceSection: some View {
        collapsibleSection("Voices", defaultExpanded: false) {
            if availableVoices.isEmpty {
                HStack {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("Loading voices...")
                        .font(.caption)
                        .foregroundStyle(Color.textMuted)
                }
                .frame(maxWidth: .infinity)
                .padding()
            } else {
                VoicePickerView(
                    tone: style.tone,
                    voiceConfig: $voiceConfig,
                    availableVoices: availableVoices
                )
            }
        }
        .padding(.horizontal)
    }

    private var audioSection: some View {
        collapsibleSection("Audio Production", defaultExpanded: false) {
            AudioProductionView(config: $audioConfig)
        }
        .padding(.horizontal)
    }

    private func collapsibleSection<Content: View>(
        _ title: String,
        defaultExpanded: Bool = true,
        @ViewBuilder content: @escaping () -> Content
    ) -> some View {
        VStack(spacing: 0) {
            Button {
                withAnimation(.snappy(duration: 0.25)) {
                    if expandedSections.contains(title) {
                        expandedSections.remove(title)
                    } else {
                        expandedSections.insert(title)
                    }
                }
            } label: {
                HStack {
                    Text(title)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Color.textPrimary)
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(Color.textMuted)
                        .rotationEffect(expandedSections.contains(title) ? .degrees(90) : .zero)
                }
                .padding()
            }
            .buttonStyle(.plain)

            if expandedSections.contains(title) {
                VStack(spacing: 16) {
                    content()
                }
                .padding(.horizontal)
                .padding(.bottom, 16)
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .background(Color.surface, in: .rect(cornerRadius: 12))
        .onAppear {
            if defaultExpanded {
                expandedSections.insert(title)
            }
        }
    }

    private func loadVoices() async {
        do {
            let response = try await APIClient.shared.getVoices()
            await MainActor.run {
                availableVoices = response.voices
            }
        } catch {
            // Silently fail - voices section will show loading state
        }
    }
}
