"""Passaggio automatico a Cloudflare dei circoli in attesa.

passaggi_cloudflare.json elenca i circoli (per nome, come in circoli.json) con il loro nuovo
indirizzo. Quando il PC del circolo installa la versione con Cloudflare, il nuovo indirizzo
comincia a rispondere e il vecchio (ngrok) smette: appena /stato_pubblico risponde dal nuovo
indirizzo, qui si cambia circoli.json e si toglie il circolo dalla lista d'attesa.
Esce con 0 se ha cambiato qualcosa (da pubblicare), 1 se non c'e' niente da fare.
"""
import json
import sys
import urllib.request

ATTESA = "passaggi_cloudflare.json"
ELENCO = "circoli.json"


def risponde(url: str) -> bool:
    try:
        req = urllib.request.Request(url.rstrip("/") + "/stato_pubblico",
                                     headers={"User-Agent": "burraco-elenco-circoli"})
        with urllib.request.urlopen(req, timeout=15) as r:
            dati = json.loads(r.read().decode("utf-8"))
        return r.status == 200 and "nome_circolo" in dati
    except Exception as e:
        print(f"  {url}: non ancora ({e.__class__.__name__})")
        return False


def main() -> int:
    with open(ATTESA, encoding="utf-8") as f:
        attesa = json.load(f)
    if not attesa:
        print("Nessun circolo in attesa.")
        return 1
    with open(ELENCO, encoding="utf-8") as f:
        elenco = json.load(f)

    cambiato = False
    for nome, nuovo in list(attesa.items()):
        circolo = next((c for c in elenco if c.get("nome") == nome), None)
        if circolo is None:
            print(f"{nome}: non e' nell'elenco, lo tolgo dall'attesa")
            del attesa[nome]
            cambiato = True
            continue
        if circolo.get("url") == nuovo:
            print(f"{nome}: gia' su {nuovo}")
            del attesa[nome]
            cambiato = True
            continue
        print(f"{nome}: provo {nuovo}")
        if risponde(nuovo):
            print(f"  {nome}: risponde -> {circolo.get('url')} diventa {nuovo}")
            vecchi = circolo.setdefault("url_precedenti", [])
            if circolo.get("url") and circolo["url"] not in vecchi:
                vecchi.append(circolo["url"])   # l'app riconosce il circolo salvato anche da qui
            circolo["url"] = nuovo
            del attesa[nome]
            cambiato = True

    if not cambiato:
        return 1
    with open(ELENCO, "w", encoding="utf-8") as f:
        json.dump(elenco, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(ATTESA, "w", encoding="utf-8") as f:
        json.dump(attesa, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
