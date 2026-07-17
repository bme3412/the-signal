import SwiftUI

struct PlayerView: View {
    let episode: Episode
    @Environment(AudioManager.self) private var audio
    @State private var showingScript = false
    @State private var showingWalkSheet = false

    private var isWalkingThisEpisode: Bool {
        audio.isWalkMode && audio.currentEpisode?.id == episode.id
    }

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            artwork
                .padding(.bottom, 32)

            metadata
                .padding(.bottom, 24)

            if isWalkingThisEpisode {
                walkStatusCard
                    .padding(.horizontal)
                    .padding(.bottom, 24)
            } else if let script = episode.script {
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

            if !isWalkingThisEpisode {
                rateSelector
                    .padding(.bottom, 24)
            }

            bottomActions

            Spacer()
        }
        .padding()
        .background(Color.background)
        .sheet(isPresented: $showingScript) {
            if let script = episode.script {
                TranscriptView(script: script, title: "Transcript")
            }
        }
        .sheet(isPresented: $showingWalkSheet) {
            WalkPlanSheet(episode: episode)
                .environment(audio)
        }
    }

    // MARK: - Walk Status

    private var walkStatusCard: some View {
        HStack(spacing: 12) {
            Image(systemName: "figure.walk")
                .font(.title3)
                .foregroundStyle(Color.accentBlue)
                .symbolEffect(.pulse, isActive: audio.isPlaying)

            VStack(alignment: .leading, spacing: 2) {
                Text(audio.currentWalkChapter?.title ?? "Done")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(Color.textPrimary)
                    .lineLimit(1)
                if let walk = audio.walk {
                    Text(walkDetail(walk))
                        .font(.caption2.monospaced())
                        .foregroundStyle(Color.textMuted)
                }
            }

            Spacer()

            Button {
                audio.endWalk()
            } label: {
                Text("End")
                    .font(.caption.weight(.medium))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(Color.surface, in: .capsule)
                    .foregroundStyle(Color.textSecondary)
            }
            .buttonStyle(.plain)
        }
        .padding(12)
        .background(Color.accentBlue.opacity(0.1), in: .rect(cornerRadius: 12))
    }

    private func walkDetail(_ walk: WalkState) -> String {
        let played = walk.playedIndices.count
        let total = played + walk.queue.count
        var parts = ["Chapter \(min(played + 1, total)) of \(total)"]
        if let distance = audio.routeTracker?.distanceText() {
            parts.append(distance)
        } else {
            parts.append("ends \(walk.targetEnd.formatted(date: .omitted, time: .shortened))")
        }
        if walk.plan.rate != 1.0 {
            parts.append(String(format: "%.2fx", walk.plan.rate))
        }
        let skipped = walk.plan.skippedIndices.count
        if skipped > 0 {
            parts.append("\(skipped) bonus skipped")
        }
        return parts.joined(separator: " · ")
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
            Text(episode.displayTitle)
                .font(.title3.weight(.semibold))
                .foregroundStyle(Color.textPrimary)
                .multilineTextAlignment(.center)
                .lineLimit(2)
                .padding(.horizontal, 24)
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
            if episode.status == .ready && !isWalkingThisEpisode {
                Button { showingWalkSheet = true } label: {
                    Label("Walk", systemImage: "figure.walk")
                        .font(.subheadline)
                        .foregroundStyle(Color.textSecondary)
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
