import AVFoundation
import MediaPlayer
import Observation

@Observable
final class AudioManager: NSObject {
    var currentEpisode: Episode?
    var isPlaying = false
    var currentTime: TimeInterval = 0
    var duration: TimeInterval = 0
    var playbackRate: Float = 1.0

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
            let localURL = try await APIClient.shared.downloadAudio(episodeId: episode.id)
            try loadAudio(from: localURL)
            currentEpisode = episode
            resume()
        } catch {
            print("AudioManager: Failed to play episode — \(error)")
        }
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
        player.currentTime = max(0, min(time, player.duration))
        currentTime = player.currentTime
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
        duration = player?.duration ?? 0
        currentTime = 0
    }

    // MARK: - Time Updates

    private func startTimeUpdates() {
        stopTimeUpdates()
        displayLink = Timer.scheduledTimer(withTimeInterval: 0.25, repeats: true) { [weak self] _ in
            guard let self, let player = self.player else { return }
            self.currentTime = player.currentTime
        }
    }

    private func stopTimeUpdates() {
        displayLink?.invalidate()
        displayLink = nil
    }

    // MARK: - Now Playing

    private func updateNowPlaying() {
        var info = [String: Any]()
        info[MPMediaItemPropertyTitle] = currentEpisode.map { "The Signal — \($0.id.prefix(8))" } ?? "The Signal"
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
        isPlaying = false
        currentTime = duration
        stopTimeUpdates()
        updateNowPlaying()
    }
}
