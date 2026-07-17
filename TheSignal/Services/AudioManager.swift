import AVFoundation
import MapKit
import MediaPlayer
import Observation

/// State of an adaptive walk session: chapters play sequentially from a
/// local queue, replanned at every chapter boundary against the wall-clock
/// deadline.
struct WalkState {
    let manifest: EpisodeManifest
    let chapterURLs: [Int: URL]
    /// Wall-clock deadline; fixed in timer mode, slides with live walking ETA
    /// in route mode.
    var targetEnd: Date
    var plan: AdaptivePlan
    /// Planned chapter indices still to play; queue[0] is the current chapter.
    var queue: [Int]
    var playedIndices: Set<Int> = []
    /// Nominal (1x) seconds of completed chapters + gaps, for progress display.
    var playedSeconds: TimeInterval = 0
}

@Observable
final class AudioManager: NSObject {
    var currentEpisode: Episode?
    var isPlaying = false
    var currentTime: TimeInterval = 0
    var duration: TimeInterval = 0
    var playbackRate: Float = 1.0
    var walk: WalkState?
    var routeTracker: RouteTracker?

    var isWalkMode: Bool { walk != nil }

    var currentWalkChapter: ManifestChapter? {
        guard let walk, let index = walk.queue.first else { return nil }
        return walk.manifest.chapters.first { $0.index == index }
    }

    private var player: AVAudioPlayer?
    private var displayLink: Timer?

    static let availableRates: [Float] = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

    override init() {
        super.init()
        setupAudioSession()
        setupRemoteCommands()
    }

    // MARK: - Playback Controls

    func play(episode: Episode) async {
        do {
            routeTracker?.stopTracking()
            routeTracker = nil
            walk = nil
            let localURL = try await APIClient.shared.downloadAudio(episodeId: episode.id)
            try loadAudio(from: localURL)
            currentEpisode = episode
            resume()
        } catch {
            print("AudioManager: Failed to play episode — \(error)")
        }
    }

    // MARK: - Walk Mode (adaptive playback)

    /// Fetch the chapter manifest, download chapter audio, and play an
    /// adaptive plan that ends within `budgetMinutes` from now.
    func startWalk(episode: Episode, budgetMinutes: Int) async {
        await startWalk(episode: episode, budgetSeconds: TimeInterval(budgetMinutes) * 60)
    }

    /// Route mode: the budget comes from the walking ETA to `destination`,
    /// and live location updates slide the deadline while you walk.
    func startWalk(episode: Episode, destination: MKMapItem, tracker: RouteTracker) async {
        do {
            let eta = try await tracker.walkingETA(to: destination)
            await startWalk(episode: episode, budgetSeconds: eta)
            guard walk != nil else { return }
            routeTracker = tracker
            tracker.startTracking(destination: destination) { [weak self] eta in
                self?.updateWalkDeadline(Date().addingTimeInterval(eta))
            }
        } catch {
            print("AudioManager: Failed to get walking ETA — \(error)")
        }
    }

    private func startWalk(episode: Episode, budgetSeconds: TimeInterval) async {
        do {
            let manifest = try await APIClient.shared.getManifest(episodeId: episode.id)
            var urls: [Int: URL] = [:]
            for chapter in manifest.chapters {
                urls[chapter.index] = try await APIClient.shared.downloadChapterAudio(
                    episodeId: episode.id, chapter: chapter
                )
            }

            let plan = AdaptivePlanner.plan(chapters: manifest.chapters, budgetSeconds: budgetSeconds)
            walk = WalkState(
                manifest: manifest,
                chapterURLs: urls,
                targetEnd: Date().addingTimeInterval(budgetSeconds),
                plan: plan,
                queue: plan.chapterIndices
            )
            currentEpisode = episode
            duration = plan.contentSeconds
            currentTime = 0
            playCurrentWalkChapter()
        } catch {
            print("AudioManager: Failed to start walk mode — \(error)")
        }
    }

    /// Slide the deadline (new walking ETA came in) and immediately retune
    /// the playback rate so the remaining content lands on it. Chapter
    /// add/drop decisions still happen at chapter boundaries.
    func updateWalkDeadline(_ end: Date) {
        guard var w = walk else { return }
        w.targetEnd = end

        if let player, !w.queue.isEmpty {
            let currentRemaining = max(0, player.duration - player.currentTime)
            let upcoming = w.manifest.chapters.filter { w.queue.dropFirst().contains($0.index) }
            let upcomingSeconds = upcoming.reduce(0) { $0 + $1.durationSeconds }
                + Double(upcoming.count) * AdaptivePlanner.chapterGapSeconds
            let content = currentRemaining + upcomingSeconds
            let rate = AdaptivePlanner.liveRate(
                contentSeconds: content,
                wallClockSeconds: end.timeIntervalSinceNow
            )
            w.plan.rate = rate
            playbackRate = rate
            player.rate = rate
        }
        walk = w
    }

    func endWalk() {
        routeTracker?.stopTracking()
        routeTracker = nil
        walk = nil
        stop()
    }

    private func playCurrentWalkChapter() {
        guard let walk, let index = walk.queue.first, let url = walk.chapterURLs[index] else {
            walkDidFinish()
            return
        }
        do {
            try loadAudio(from: url)
            playbackRate = walk.plan.rate
            resume()
        } catch {
            print("AudioManager: Failed to play chapter \(index) — \(error)")
        }
    }

    /// Called when a chapter finishes: mark it played, replan the remaining
    /// chapters against the time left, and start the next one. Replanning can
    /// re-add an optional chapter if the walk is going slower than expected,
    /// or drop one if time is running short.
    private func advanceWalkChapter() {
        guard var w = walk, let finished = w.queue.first else { return }
        if let chapter = w.manifest.chapters.first(where: { $0.index == finished }) {
            w.playedSeconds += chapter.durationSeconds + AdaptivePlanner.chapterGapSeconds
        }
        w.playedIndices.insert(finished)
        w.queue.removeFirst()

        let candidates = w.manifest.chapters.filter { $0.index > finished }
        guard !candidates.isEmpty else {
            walk = w
            walkDidFinish()
            return
        }

        let plan = AdaptivePlanner.plan(
            chapters: candidates,
            budgetSeconds: w.targetEnd.timeIntervalSinceNow
        )
        w.plan = plan
        w.queue = plan.chapterIndices
        walk = w
        duration = w.playedSeconds + plan.contentSeconds
        playCurrentWalkChapter()
    }

    private func walkDidFinish() {
        routeTracker?.stopTracking()
        isPlaying = false
        currentTime = duration
        stopTimeUpdates()
        updateNowPlaying()
    }

    func pause() {
        player?.pause()
        isPlaying = false
        stopTimeUpdates()
        updateNowPlaying()
    }

    func resume() {
        player?.rate = playbackRate
        player?.play()
        isPlaying = true
        startTimeUpdates()
        updateNowPlaying()
    }

    func toggle() {
        if isPlaying { pause() } else { resume() }
    }

    func skip(seconds: TimeInterval) {
        guard let player else { return }
        let target = max(0, min(player.currentTime + seconds, player.duration))
        player.currentTime = target
        currentTime = target
        updateNowPlaying()
    }

    func seek(to time: TimeInterval) {
        guard let player else { return }
        if let walk {
            // Global time -> position within the current chapter, clamped to
            // its bounds; walk mode never jumps across chapters.
            let inChapter = max(0, min(time - walk.playedSeconds, player.duration))
            player.currentTime = inChapter
            currentTime = walk.playedSeconds + inChapter
        } else {
            player.currentTime = max(0, min(time, player.duration))
            currentTime = player.currentTime
        }
        updateNowPlaying()
    }

    func setRate(_ rate: Float) {
        playbackRate = rate
        player?.rate = rate
        if !(player?.isPlaying ?? false), isPlaying {
            player?.play()
        }
        updateNowPlaying()
    }

    func stop() {
        player?.stop()
        player = nil
        routeTracker?.stopTracking()
        routeTracker = nil
        walk = nil
        isPlaying = false
        currentTime = 0
        duration = 0
        currentEpisode = nil
        stopTimeUpdates()
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }

    // MARK: - Audio Session

    private func setupAudioSession() {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .spokenAudio)
            try session.setActive(true)
        } catch {
            print("AudioManager: Audio session setup failed — \(error)")
        }
    }

    private func loadAudio(from url: URL) throws {
        player?.stop()
        player = try AVAudioPlayer(contentsOf: url)
        player?.delegate = self
        player?.enableRate = true
        player?.prepareToPlay()
        if walk == nil {
            duration = player?.duration ?? 0
            currentTime = 0
        }
    }

    // MARK: - Time Updates

    private func startTimeUpdates() {
        stopTimeUpdates()
        displayLink = Timer.scheduledTimer(withTimeInterval: 0.25, repeats: true) { [weak self] _ in
            guard let self, let player = self.player else { return }
            if let walk = self.walk {
                self.currentTime = walk.playedSeconds + player.currentTime
            } else {
                self.currentTime = player.currentTime
            }
        }
    }

    private func stopTimeUpdates() {
        displayLink?.invalidate()
        displayLink = nil
    }

    // MARK: - Now Playing

    private func updateNowPlaying() {
        var info = [String: Any]()
        if let chapter = currentWalkChapter {
            info[MPMediaItemPropertyTitle] = "\(currentEpisode?.title ?? "The Signal") — \(chapter.title)"
        } else {
            info[MPMediaItemPropertyTitle] = currentEpisode?.displayTitle ?? "The Signal"
        }
        info[MPMediaItemPropertyArtist] = "The Signal"
        info[MPMediaItemPropertyPlaybackDuration] = duration
        info[MPNowPlayingInfoPropertyElapsedPlaybackTime] = currentTime
        info[MPNowPlayingInfoPropertyPlaybackRate] = isPlaying ? playbackRate : 0.0
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    private func setupRemoteCommands() {
        let center = MPRemoteCommandCenter.shared()

        center.playCommand.addTarget { [weak self] _ in
            self?.resume()
            return .success
        }
        center.pauseCommand.addTarget { [weak self] _ in
            self?.pause()
            return .success
        }
        center.togglePlayPauseCommand.addTarget { [weak self] _ in
            self?.toggle()
            return .success
        }
        center.skipForwardCommand.preferredIntervals = [15]
        center.skipForwardCommand.addTarget { [weak self] _ in
            self?.skip(seconds: 15)
            return .success
        }
        center.skipBackwardCommand.preferredIntervals = [15]
        center.skipBackwardCommand.addTarget { [weak self] _ in
            self?.skip(seconds: -15)
            return .success
        }
        center.changePlaybackPositionCommand.addTarget { [weak self] event in
            guard let event = event as? MPChangePlaybackPositionCommandEvent else { return .commandFailed }
            self?.seek(to: event.positionTime)
            return .success
        }
    }
}

// MARK: - AVAudioPlayerDelegate

extension AudioManager: AVAudioPlayerDelegate {
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        if isWalkMode {
            advanceWalkChapter()
            return
        }
        isPlaying = false
        currentTime = duration
        stopTimeUpdates()
        updateNowPlaying()
    }
}
