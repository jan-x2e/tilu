# Ruokalista-sivusto

Hakee automaattisesti viikon ruokalistan [aromi.hel.fi](https://aromi.hel.fi)-palvelusta ja julkaisee sen staattisena HTML-sivuna Netlifyssa.

## Rakenne

```
generate.py        ← Hakee ruokalistan ja generoi index.html
index.html         ← Generoitu sivu (ei muokata käsin)
.github/
  workflows/
    update.yml     ← Automaattinen päivitys ma-pe klo 7
```

## Käyttöönotto

### 1. GitHub-repositorio
Luo uusi repositorio GitHubiin ja pushaa tiedostot sinne.

### 2. Netlify-sivusto
1. Mene [app.netlify.com](https://app.netlify.com)
2. **Add new site → Import an existing project → GitHub**
3. Valitse tämä repositorio
4. Build command: `python generate.py`
5. Publish directory: `.` (piste)
6. **Deploy site**

### 3. GitHub Secrets
Jotta GitHub Actions voi deployata Netlifyyn, tarvitaan kaksi salaisuutta:

**Netlify Auth Token:**
1. Netlify → User settings → Applications → Personal access tokens
2. Luo uusi token, kopioi se
3. GitHub → Settings → Secrets → Actions → `NETLIFY_AUTH_TOKEN`

**Netlify Site ID:**
1. Netlify → Site configuration → Site ID
2. GitHub → Settings → Secrets → Actions → `NETLIFY_SITE_ID`

### 4. Valmis!
Sivu päivittyy automaattisesti arkisin klo 7. Voit myös triggeröidä päivityksen käsin:
GitHub → Actions → "Päivitä ruokalista" → Run workflow

## Paikallinen testaus

```bash
pip install playwright
python -m playwright install chromium
python generate.py
# Avaa index.html selaimessa
```
