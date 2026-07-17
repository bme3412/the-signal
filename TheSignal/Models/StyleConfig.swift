import SwiftUI

// MARK: - Style Dimensions

enum Depth: String, Codable, CaseIterable, Identifiable {
    case briefing
    case deepDive = "deep_dive"
    case synthesis

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .briefing: "Briefing"
        case .deepDive: "Deep Dive"
        case .synthesis: "Synthesis"
        }
    }

    var icon: String {
        switch self {
        case .briefing: "list.bullet"
        case .deepDive: "magnifyingglass"
        case .synthesis: "link"
        }
    }

    var shortDescription: String {
        switch self {
        case .briefing: "Hit every story, keep it moving"
        case .deepDive: "Go deep on what matters most"
        case .synthesis: "Find the thread across stories"
        }
    }

    var color: Color {
        switch self {
        case .briefing: .blue
        case .deepDive: .purple
        case .synthesis: .orange
        }
    }
}

enum Tone: String, Codable, CaseIterable, Identifiable {
    case casual, polished, debate, technical

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .casual: "Casual"
        case .polished: "Polished"
        case .debate: "Debate"
        case .technical: "Technical"
        }
    }

    var icon: String {
        switch self {
        case .casual: "person.2.fill"
        case .polished: "person.2.wave.2.fill"
        case .debate: "arrow.left.arrow.right"
        case .technical: "wrench.and.screwdriver.fill"
        }
    }

    var shortDescription: String {
        switch self {
        case .casual: "Two hosts, natural banter"
        case .polished: "NPR-style anchor + analyst"
        case .debate: "Bull vs Bear, opposing views"
        case .technical: "Two engineers, deep dive"
        }
    }

    var color: Color {
        switch self {
        case .casual: .green
        case .polished: .blue
        case .debate: .red
        case .technical: .purple
        }
    }
}

enum Lens: String, Codable, CaseIterable, Identifiable {
    case investor, engineer, macro, general

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .investor: "Investor"
        case .engineer: "Engineer"
        case .macro: "Macro"
        case .general: "General"
        }
    }

    var icon: String {
        switch self {
        case .investor: "chart.line.uptrend.xyaxis"
        case .engineer: "cpu"
        case .macro: "globe"
        case .general: "person.fill"
        }
    }

    var shortDescription: String {
        switch self {
        case .investor: "Revenue, TAM, valuation"
        case .engineer: "Architecture, moats, tradeoffs"
        case .macro: "Policy, supply chains, trends"
        case .general: "Why it matters to everyone"
        }
    }

    var color: Color {
        switch self {
        case .investor: .green
        case .engineer: .cyan
        case .macro: .orange
        case .general: .blue
        }
    }
}

enum Pacing: String, Codable, CaseIterable, Identifiable {
    case rapid, measured, variable

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .rapid: "Rapid"
        case .measured: "Measured"
        case .variable: "Variable"
        }
    }

    var icon: String {
        switch self {
        case .rapid: "hare.fill"
        case .measured: "tortoise.fill"
        case .variable: "waveform"
        }
    }

    var shortDescription: String {
        switch self {
        case .rapid: "High energy, punchy"
        case .measured: "Let ideas breathe"
        case .variable: "Fast facts, slow analysis"
        }
    }

    var color: Color {
        switch self {
        case .rapid: .red
        case .measured: .blue
        case .variable: .purple
        }
    }
}

enum Humor: String, Codable, CaseIterable, Identifiable {
    case serious, dry, playful, roast

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .serious: "Serious"
        case .dry: "Dry"
        case .playful: "Playful"
        case .roast: "Roast"
        }
    }

    var icon: String {
        switch self {
        case .serious: "briefcase.fill"
        case .dry: "face.smiling"
        case .playful: "sparkles"
        case .roast: "flame.fill"
        }
    }

    var shortDescription: String {
        switch self {
        case .serious: "Content is the entertainment"
        case .dry: "Deadpan, note the ironies"
        case .playful: "Analogies, pop culture refs"
        case .roast: "Sharp, opinionated takes"
        }
    }

    var color: Color {
        switch self {
        case .serious: .gray
        case .dry: .blue
        case .playful: .yellow
        case .roast: .red
        }
    }
}

enum Audience: String, Codable, CaseIterable, Identifiable {
    case insider, informed, curious

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .insider: "Insider"
        case .informed: "Informed"
        case .curious: "Curious"
        }
    }

    var icon: String {
        switch self {
        case .insider: "lock.fill"
        case .informed: "newspaper.fill"
        case .curious: "questionmark.circle.fill"
        }
    }

    var shortDescription: String {
        switch self {
        case .insider: "Skip the basics, use shorthand"
        case .informed: "Brief framing, one line max"
        case .curious: "Define terms naturally"
        }
    }

    var color: Color {
        switch self {
        case .insider: .purple
        case .informed: .blue
        case .curious: .green
        }
    }
}

enum Structure: String, Codable, CaseIterable, Identifiable {
    case narrative, ranked, thematic, contrarian

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .narrative: "Narrative"
        case .ranked: "Ranked"
        case .thematic: "Thematic"
        case .contrarian: "Contrarian"
        }
    }

    var icon: String {
        switch self {
        case .narrative: "book.fill"
        case .ranked: "list.number"
        case .thematic: "square.grid.2x2.fill"
        case .contrarian: "arrow.uturn.backward"
        }
    }

    var shortDescription: String {
        switch self {
        case .narrative: "Story arc to climactic insight"
        case .ranked: "Biggest story first"
        case .thematic: "Group by theme, not article"
        case .contrarian: "What everyone gets wrong"
        }
    }

    var color: Color {
        switch self {
        case .narrative: .orange
        case .ranked: .blue
        case .thematic: .purple
        case .contrarian: .red
        }
    }
}

enum Closer: String, Codable, CaseIterable, Identifiable {
    case actionable, philosophical, prediction, question

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .actionable: "Actionable"
        case .philosophical: "Philosophical"
        case .prediction: "Prediction"
        case .question: "Question"
        }
    }

    var icon: String {
        switch self {
        case .actionable: "checkmark.circle.fill"
        case .philosophical: "brain.head.profile"
        case .prediction: "chart.line.uptrend.xyaxis"
        case .question: "questionmark.bubble.fill"
        }
    }

    var shortDescription: String {
        switch self {
        case .actionable: "2-3 specific action items"
        case .philosophical: "Decade-level implications"
        case .prediction: "Bold, falsifiable prediction"
        case .question: "Open question to ponder"
        }
    }

    var color: Color {
        switch self {
        case .actionable: .green
        case .philosophical: .purple
        case .prediction: .orange
        case .question: .cyan
        }
    }
}

// MARK: - StyleConfig

struct StyleConfig: Codable, Equatable {
    var depth: Depth = .briefing
    var tone: Tone = .casual
    var lens: Lens = .investor
    var pacing: Pacing = .variable
    var humor: Humor = .dry
    var audience: Audience = .informed
    var structure: Structure = .ranked
    var closer: Closer = .actionable
}

// MARK: - Presets

struct StylePreset: Identifiable {
    let id: String
    let name: String
    let subtitle: String
    let icon: String
    let gradient: [Color]
    let config: StyleConfig
}

extension StyleConfig {
    static let morningBrief = StyleConfig(
        depth: .briefing, tone: .polished, lens: .investor,
        pacing: .rapid, humor: .serious, audience: .insider,
        structure: .ranked, closer: .actionable
    )

    static let deepCut = StyleConfig(
        depth: .deepDive, tone: .technical, lens: .engineer,
        pacing: .measured, humor: .dry, audience: .insider,
        structure: .narrative, closer: .prediction
    )

    static let hotTake = StyleConfig(
        depth: .synthesis, tone: .debate, lens: .investor,
        pacing: .variable, humor: .roast, audience: .informed,
        structure: .contrarian, closer: .prediction
    )

    static let explainIt = StyleConfig(
        depth: .synthesis, tone: .casual, lens: .general,
        pacing: .variable, humor: .playful, audience: .curious,
        structure: .thematic, closer: .question
    )

    static let presets: [StylePreset] = [
        StylePreset(
            id: "morning", name: "Morning Brief",
            subtitle: "Fast, polished, investor-grade",
            icon: "sunrise.fill",
            gradient: [.blue, .cyan],
            config: .morningBrief
        ),
        StylePreset(
            id: "deep", name: "Deep Cut",
            subtitle: "Technical deep-dive, measured pace",
            icon: "magnifyingglass",
            gradient: [.purple, .indigo],
            config: .deepCut
        ),
        StylePreset(
            id: "hot", name: "Hot Take",
            subtitle: "Debate format, sharp opinions",
            icon: "flame.fill",
            gradient: [.red, .orange],
            config: .hotTake
        ),
        StylePreset(
            id: "explain", name: "Explain It",
            subtitle: "Casual, curious, big picture",
            icon: "lightbulb.fill",
            gradient: [.yellow, .green],
            config: .explainIt
        ),
    ]
}
