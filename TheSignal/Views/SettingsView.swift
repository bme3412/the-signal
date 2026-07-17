import SwiftUI

struct SettingsView: View {
    @AppStorage(APIClient.baseURLDefaultsKey) private var backendURL = APIClient.defaultBaseURL
    @State private var health: HealthResponse?
    @State private var checking = false
    @State private var checkError: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("http://192.168.1.20:8000", text: $backendURL)
                        .keyboardType(.URL)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                        .font(.body.monospaced())
                        .onSubmit { testConnection() }

                    Button {
                        testConnection()
                    } label: {
                        HStack {
                            Text(checking ? "Checking…" : "Test Connection")
                            if checking {
                                Spacer()
                                ProgressView()
                                    .controlSize(.small)
                            }
                        }
                    }
                    .disabled(checking)
                } header: {
                    Text("Backend URL")
                } footer: {
                    Text(
                        "On a real iPhone, use your Mac's LAN IP (not localhost) and run "
                        + "the backend with: uvicorn main:app --host 0.0.0.0"
                    )
                }

                if health != nil || checkError != nil {
                    Section("Status") {
                        if let health {
                            statusRow("Server", ok: health.status == "ok")
                            statusRow("Anthropic key", ok: health.anthropicConfigured)
                            statusRow("ElevenLabs key", ok: health.elevenlabsConfigured)
                        }
                        if let checkError {
                            Label(checkError, systemImage: "xmark.octagon.fill")
                                .font(.caption)
                                .foregroundStyle(Color.red)
                        }
                    }
                }
            }
            .navigationTitle("Settings")
        }
        .task {
            // Sync the stored URL into the client on first appearance, in case
            // it was edited without hitting Test.
            await APIClient.shared.setBaseURL(normalized(backendURL))
        }
    }

    private func statusRow(_ label: String, ok: Bool) -> some View {
        HStack {
            Text(label)
            Spacer()
            Image(systemName: ok ? "checkmark.circle.fill" : "xmark.circle.fill")
                .foregroundStyle(ok ? Color.green : Color.orange)
        }
    }

    private func testConnection() {
        let url = normalized(backendURL)
        backendURL = url
        checking = true
        health = nil
        checkError = nil
        Task {
            await APIClient.shared.setBaseURL(url)
            do {
                health = try await APIClient.shared.checkHealth()
            } catch {
                checkError = error.localizedDescription
            }
            checking = false
        }
    }

    private func normalized(_ raw: String) -> String {
        var url = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        if url.isEmpty { return APIClient.defaultBaseURL }
        if !url.contains("://") {
            url = "http://" + url
        }
        while url.hasSuffix("/") {
            url.removeLast()
        }
        return url
    }
}
