# Release-Anleitung

Releases entstehen automatisch: Tag `vX.Y.Z` auf `main` pushen → GitHub Actions
(`.github/workflows/release.yml`) baut die Binaries für Linux, Windows und
macOS, erzeugt `SHA256SUMS.txt`, attestiert alle Assets (Sigstore,
`actions/attest-build-provenance`) und veröffentlicht das Release samt
„Checksums“-Abschnitt in den Release-Notes.

## Manueller Schritt pro Release: PGP-Signaturen

Die Assets werden zusätzlich mit PGP signiert. Das passiert ausschließlich
**lokal** — der private Schlüssel gehört niemals ins Repo, in Workflows oder
GitHub-Secrets.

Wichtig: Immer die **veröffentlichten** Assets signieren (erst herunterladen,
dann signieren) — nie einen frischen lokalen Build. Ein neuer Build hätte
andere Hashes, und Signatur bzw. `SHA256SUMS.txt` würden bei allen Nutzern
fehlschlagen.

```bash
# 1. Assets des frisch veröffentlichten Releases herunterladen
gh release download vX.Y.Z --dir dist-signing
cd dist-signing

# 2. Jede Datei signieren (erzeugt jeweils <datei>.asc)
for f in *; do gpg --detach-sign --armor "$f"; done

# 3. Signaturen ans Release anhängen (neben Assets + SHA256SUMS.txt)
gh release upload vX.Y.Z *.asc
```

Der zugehörige Public Key ist für Nutzer unter <https://tertlidis.com/pgp.asc>
abrufbar (Fingerprint `D251 773E 1DF7 0C1D 0476  1CB0 F92A F40D 80E8 5351`);
die Prüf-Kommandos stehen im README unter „Verify your download“.
