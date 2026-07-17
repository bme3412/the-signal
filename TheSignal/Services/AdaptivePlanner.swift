import Foundation

/// Anything the planner needs to know about a chapter. `ManifestChapter`
/// conforms; tests can use lightweight stubs.
protocol PlannableChapter {
    var index: Int { get }
    var role: ChapterRole { get }
    var durationSeconds: Double { get }
}

struct AdaptivePlan {
    /// Chapter indices to play, in order. Intro/core/closer always included.
    var chapterIndices: [Int]
    /// Optional chapters dropped to fit the budget.
    var skippedIndices: [Int]
    /// Playback rate that closes the residual gap, clamped to an
    /// imperceptible range.
    var rate: Float
    /// Audio content at 1x, including inter-chapter gaps.
    var contentSeconds: Double
    /// Time the plan actually takes at `rate`.
    var wallClockSeconds: Double
    /// True when even the required chapters at max rate exceed the budget.
    var overBudget: Bool
}

/// Fits chapters into a wall-clock budget: required chapters (intro, core,
/// closer) always play; optional chapters are kept in narrative order while
/// they still fit; playback rate absorbs the remainder.
enum AdaptivePlanner {
    static let minRate: Double = 0.95
    static let maxRate: Double = 1.10
    static let chapterGapSeconds: Double = 0.3

    /// Rate that lands `contentSeconds` of audio on a wall-clock window,
    /// clamped to the imperceptible range. Used for mid-chapter retuning
    /// when a live walking ETA slides the deadline.
    static func liveRate(contentSeconds: Double, wallClockSeconds: Double) -> Float {
        let raw = wallClockSeconds > 0 ? contentSeconds / wallClockSeconds : maxRate
        return Float(min(max(raw, minRate), maxRate))
    }

    static func plan(
        chapters: [any PlannableChapter],
        budgetSeconds: Double,
        gapSeconds: Double = chapterGapSeconds
    ) -> AdaptivePlan {
        func totalSeconds(_ chs: [any PlannableChapter]) -> Double {
            guard !chs.isEmpty else { return 0 }
            let audio = chs.reduce(0) { $0 + $1.durationSeconds }
            return audio + Double(chs.count - 1) * gapSeconds
        }

        var chosen = chapters.filter { $0.role != .optional }
        var skipped: [Int] = []

        for opt in chapters.filter({ $0.role == .optional }) {
            let candidate = (chosen + [opt]).sorted { $0.index < $1.index }
            if totalSeconds(candidate) / maxRate <= budgetSeconds {
                chosen = candidate
            } else {
                skipped.append(opt.index)
            }
        }
        chosen.sort { $0.index < $1.index }

        let content = totalSeconds(chosen)
        let rawRate = budgetSeconds > 0 ? content / budgetSeconds : maxRate
        let rate = min(max(rawRate, minRate), maxRate)

        return AdaptivePlan(
            chapterIndices: chosen.map(\.index),
            skippedIndices: skipped.sorted(),
            rate: Float(rate),
            contentSeconds: content,
            wallClockSeconds: content / rate,
            overBudget: content / maxRate > budgetSeconds + 1
        )
    }
}
