import SwiftUI

struct GenerateView: View {
    @Environment(ArticleStore.self) private var store
    @Environment(AudioManager.self) private var audio
    @State private var style = StyleConfig()
    @State private var targetMinutes = 20
    @State private var voiceConfig: [String: SpeakerConfig] = [:]
    @State private var audioConfig = AudioProductionConfig()
    @State private var generatingEpisode: Episode?
    @State private var showingPlayer = false
    @State private var errorMessage: String?

    private var selectedArticles: [Article] {
        store.selectedArticles()
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    summaryCard

                    StylePickerView(
                        style: $style,
                        targetMinutes: $targetMinutes,
                        voiceConfig: $voiceConfig,
                        audioConfig: $audioConfig
                    )

                    if let ep = generatingEpisode {
                        progressCard(ep)
                    }

                    if let errorMessage {
                        errorCard(errorMessage)
                    }
                }
                .padding(.bottom, 100)
            }
            .navigationTitle("Generate")
            .safeAreaInset(edge: .bottom) {
                generateButton
            }
            .fullScreenCover(isPresented: $showingPlayer) {
                if let ep = generatingEpisode {
                    PlayerView(episode: ep)
                }
            }
        }
    }

    // MARK: - Summary Card

    private var summaryCard: some View {
        VStack(spacing: 12) {
            HStack {
                Label("\(selectedArticles.count) articles selected", systemImage: "doc.text.fill")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(Color.textPrimary)
                Spacer()
                let totalWords = selectedArticles.reduce(0) { $0 + $1.wordCount }
                Text("\(totalWords) words")
                    .font(.caption.monospaced())
                    .foregroundStyle(Color.textMuted)
            }

            StyleSummaryBar(style: style)

            HStack {
                Text("~\(targetMinutes) min episode")
                    .font(.caption)
                    .foregroundStyle(Color.textSecondary)
                Spacer()
                let estimatedCost = Double(targetMinutes) * 0.03
                Text(String(format: "~$%.2f estimated", estimatedCost))
                    .font(.caption.monospaced())
                    .foregroundStyle(Color.textMuted)
            }
        }
        .padding()
        .background(Color.surface, in: .rect(cornerRadius: 12))
        .padding(.horizontal)
    }

    // MARK: - Generate Button

    private var generateButton: some View {
        Button(action: generate) {
            HStack {
                if generatingEpisode != nil && !(generatingEpisode?.status.isTerminal ?? true) {
                    ProgressView()
                        .tint(.white)
                        .padding(.trailing, 4)
                    Text("Generating…")
                } else {
                    Image(systemName: "wand.and.stars")
                    Text("Generate Episode")
                }
            }
            .font(.headline)
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                selectedArticles.isEmpty || (generatingEpisode != nil && !(generatingEpisode?.status.isTerminal ?? true))
                    ? Color.gray
                    : Color.accentBlue,
                in: .rect(cornerRadius: 14)
            )
        }
        .disabled(selectedArticles.isEmpty || (generatingEpisode != nil && !(generatingEpisode?.status.isTerminal ?? true)))
        .padding(.horizontal)
        .padding(.bottom, 8)
    }

    // MARK: - Progress

    private func progressCard(_ episode: Episode) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Pipeline")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Color.textPrimary)
                Spacer()
                Image(systemName: episode.status.icon)
                    .foregroundStyle(episode.status.color)
                    .symbolEffect(.pulse, isActive: !episode.status.isTerminal)
            }

            let steps: [(String, EpisodeStatus)] = [
                ("Summarizing", .summarizing),
                ("Writing Script", .scripting),
                ("Generating Audio", .synthesizing),
                ("Mixing", .mixing),
                ("Ready", .ready),
            ]

            ForEach(steps, id: \.0) { name, status in
                HStack(spacing: 10) {
                    let current = episode.status.stepIndex
                    let step = status.stepIndex
                    Image(systemName: current > step ? "checkmark.circle.fill" :
                            current == step ? "circle.dotted" : "circle")
                        .font(.body)
                        .foregroundStyle(current > step ? .green :
                                            current == step ? Color.accentBlue : Color.textMuted)

                    Text(name)
                        .font(.subheadline)
                        .foregroundStyle(current >= step ? Color.textPrimary : Color.textMuted)

                    Spacer()
                }
            }
        }
        .padding()
        .background(Color.surface, in: .rect(cornerRadius: 12))
        .padding(.horizontal)
    }

    private func errorCard(_ message: String) -> some View {
        VStack(spacing: 8) {
            Label("Generation Failed", systemImage: "exclamationmark.triangle.fill")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.red)
            Text(message)
                .font(.caption)
                .foregroundStyle(Color.textSecondary)
                .multilineTextAlignment(.center)
            Button("Retry") { generate() }
                .buttonStyle(.borderedProminent)
                .tint(.red)
        }
        .padding()
        .background(Color.red.opacity(0.1), in: .rect(cornerRadius: 12))
        .padding(.horizontal)
    }

    // MARK: - Generate Logic

    private func generate() {
        errorMessage = nil
        let articles = selectedArticles
        guard !articles.isEmpty else { return }

        let request = EpisodeRequest(
            articleIds: articles.map { $0.id.uuidString },
            style: style,
            voiceConfig: voiceConfig.isEmpty ? nil : voiceConfig,
            audioConfig: audioConfig,
            targetMinutes: targetMinutes
        )

        Task {
            do {
                let episode = try await APIClient.shared.generateEpisode(request: request)
                generatingEpisode = episode
                await pollForCompletion(episodeId: episode.id)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func pollForCompletion(episodeId: String) async {
        while true {
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            do {
                let updated = try await APIClient.shared.getEpisode(id: episodeId)
                generatingEpisode = updated

                if updated.status == .ready {
                    showingPlayer = true
                    return
                }
                if updated.status == .failed {
                    errorMessage = updated.error ?? "Unknown error"
                    return
                }
            } catch {
                errorMessage = error.localizedDescription
                return
            }
        }
    }
}
