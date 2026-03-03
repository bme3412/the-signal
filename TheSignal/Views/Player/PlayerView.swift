import SwiftUI

struct PlayerView: View {
    let episode: Episode
    @Environment(AudioManager.self) private var audio
    @State private var showingScript = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            artwork
                .padding(.bottom, 32)

            metadata
                .padding(.bottom, 24)

            if let script = episode.script {
                SegmentMap(segments: script.segments, currentTime: audio.currentTime, duration: audio.duration) { time in
                    audio.seek(to: time)
                }
                .frame(height: 32)
                .padding(.horizontal)
                .padding(.bottom, 24)
            }

            progressBar
                .padding(.horizontal)
                .padding(.bottom, 16)

            transportControls
                .padding(.bottom, 12)

            rateSelector
                .padding(.bottom, 24)

            bottomActions

            Spacer()
        }
        .padding()
        .background(Color.background)
        .sheet(isPresented: $showingScript) {
            if let script = episode.script {
                scriptSheet(script)
            }
        }
    }

    // MARK: - Artwork

    private var artwork: some View {
        RoundedRectangle(cornerRadius: 20)
            .fill(
                .linearGradient(
                    colors: [
                        episode.style.tone.color.opacity(0.6),
                        episode.style.depth.color.opacity(0.4),
                        Color.surface,
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .frame(width: 280, height: 280)
            .overlay {
                VStack(spacing: 8) {
                    Image(systemName: "waveform")
                        .font(.system(size: 48))
                        .foregroundStyle(Color.textSecondary)
                        .symbolEffect(.variableColor.iterative, isActive: audio.isPlaying)
                    Text("THE SIGNAL")
                        .font(.caption.weight(.bold).monospaced())
                        .foregroundStyle(Color.textMuted)
                        .tracking(4)
                }
            }
            .shadow(color: episode.style.tone.color.opacity(0.3), radius: 30, y: 10)
    }

    // MARK: - Metadata

    private var metadata: some View {
        VStack(spacing: 4) {
            Text("Episode \(episode.id.prefix(8))")
                .font(.title3.weight(.semibold))
                .foregroundStyle(Color.textPrimary)
            Text(episode.createdAt, style: .date)
                .font(.subheadline)
                .foregroundStyle(Color.textSecondary)
            if let dur = episode.audioDuration {
                Text(formatDuration(dur))
                    .font(.caption.monospaced())
                    .foregroundStyle(Color.textMuted)
            }
        }
    }

    // MARK: - Progress

    private var progressBar: some View {
        VStack(spacing: 4) {
            Slider(
                value: Binding(
                    get: { audio.currentTime },
                    set: { audio.seek(to: $0) }
                ),
                in: 0...max(audio.duration, 1)
            )
            .tint(Color.accentBlue)

            HStack {
                Text(formatDuration(audio.currentTime))
                Spacer()
                Text("-\(formatDuration(audio.duration - audio.currentTime))")
            }
            .font(.caption2.monospaced())
            .foregroundStyle(Color.textMuted)
        }
    }

    // MARK: - Transport

    private var transportControls: some View {
        HStack(spacing: 40) {
            Button { audio.skip(seconds: -15) } label: {
                Image(systemName: "gobackward.15")
                    .font(.title2)
                    .foregroundStyle(Color.textSecondary)
            }

            Button { audio.toggle() } label: {
                Image(systemName: audio.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                    .font(.system(size: 64))
                    .foregroundStyle(Color.textPrimary)
            }

            Button { audio.skip(seconds: 15) } label: {
                Image(systemName: "goforward.15")
                    .font(.title2)
                    .foregroundStyle(Color.textSecondary)
            }
        }
    }

    // MARK: - Rate

    private var rateSelector: some View {
        HStack(spacing: 12) {
            ForEach(AudioManager.availableRates, id: \.self) { rate in
                Button {
                    audio.setRate(rate)
                } label: {
                    Text(rate == 1.0 ? "1x" : String(format: "%.1fx", rate))
                        .font(.caption2.weight(.medium).monospaced())
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(
                            audio.playbackRate == rate ? Color.accentBlue.opacity(0.2) : Color.clear,
                            in: .capsule
                        )
                        .foregroundStyle(audio.playbackRate == rate ? Color.accentBlue : Color.textMuted)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Bottom Actions

    private var bottomActions: some View {
        HStack(spacing: 32) {
            if episode.script != nil {
                Button { showingScript = true } label: {
                    Label("Script", systemImage: "doc.text")
                        .font(.subheadline)
                        .foregroundStyle(Color.textSecondary)
                }
            }
        }
    }

    // MARK: - Script Sheet

    private func scriptSheet(_ script: EpisodeScript) -> some View {
        NavigationStack {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    ForEach(script.segments) { seg in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(seg.speaker)
                                .font(.caption.weight(.bold).monospaced())
                                .foregroundStyle(seg.speakerColor)
                            Text(seg.text)
                                .font(.body)
                                .foregroundStyle(Color.textPrimary)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Script")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { showingScript = false }
                }
            }
        }
    }

    private func formatDuration(_ seconds: TimeInterval) -> String {
        let mins = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%d:%02d", mins, secs)
    }
}
