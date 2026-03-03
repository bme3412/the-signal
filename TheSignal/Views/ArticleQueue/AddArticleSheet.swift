import SwiftUI

struct AddArticleSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(ArticleStore.self) private var store

    @State private var mode: InputMode = .url
    @State private var urlText = ""
    @State private var titleText = ""
    @State private var bodyText = ""
    @State private var isLoading = false
    @State private var errorMessage: String?

    enum InputMode: String, CaseIterable {
        case url = "URL"
        case text = "Paste Text"
    }

    var body: some View {
        NavigationStack {
            Form {
                Picker("Input", selection: $mode) {
                    ForEach(InputMode.allCases, id: \.self) { m in
                        Text(m.rawValue).tag(m)
                    }
                }
                .pickerStyle(.segmented)
                .listRowBackground(Color.clear)

                switch mode {
                case .url:
                    Section("Article URL") {
                        TextField("https://...", text: $urlText)
                            .keyboardType(.URL)
                            .textContentType(.URL)
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                    }
                case .text:
                    Section("Title") {
                        TextField("Article title", text: $titleText)
                    }
                    Section("Content") {
                        TextEditor(text: $bodyText)
                            .frame(minHeight: 200)
                    }
                }

                if let errorMessage {
                    Section {
                        Label(errorMessage, systemImage: "exclamationmark.triangle.fill")
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Add Article")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") { submit() }
                        .disabled(!canSubmit)
                        .bold()
                }
            }
            .overlay {
                if isLoading {
                    ProgressView("Fetching article…")
                        .padding()
                        .background(.regularMaterial, in: .rect(cornerRadius: 12))
                }
            }
            .disabled(isLoading)
        }
    }

    private var canSubmit: Bool {
        switch mode {
        case .url: !urlText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        case .text: !titleText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                    && !bodyText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }
    }

    private func submit() {
        errorMessage = nil
        isLoading = true

        Task {
            do {
                switch mode {
                case .url:
                    guard let url = URL(string: urlText.trimmingCharacters(in: .whitespacesAndNewlines)) else {
                        errorMessage = "Invalid URL"
                        isLoading = false
                        return
                    }
                    let dto = try await APIClient.shared.submitArticle(url: url)
                    store.addFromDTO(dto)

                case .text:
                    let dto = try await APIClient.shared.submitArticle(
                        title: titleText.trimmingCharacters(in: .whitespacesAndNewlines),
                        text: bodyText.trimmingCharacters(in: .whitespacesAndNewlines)
                    )
                    store.addFromDTO(dto)
                }
                dismiss()
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }
}
