import re
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Generador de pauta", page_icon="💊", layout="centered")
st.title("💊 Generador de pauta de medicación")
st.caption("Pega el texto del listado de medicación, incluso si está todo seguido y sin saltos de línea.")

BRAND_MAP = [
    (r"\batrovent\b", "Atrovent", "Ipratropio"),
    (r"\bfoster(?:\s+nexthaler)?\b", "Foster", "Beclometasona/Formoterol"),
    (r"\bozempic\b", "Ozempic", "Semaglutida"),
    (r"\bsynjardy\b", "Synjardy", "Empagliflozina/Metformina"),
    (r"\bduodart\b", "Duodart", "Dutasterida/Tamsulosina"),
    (r"\bnaproxeno\s+s[oó]dico\b", "Naproxeno sódico", "Naproxeno"),
    (r"\batorvastatina\s+tecnigen\b", "Atorvastatina Tecnigen", "Atorvastatina"),
    (r"\bprednisona\s+cinfa\b", "Prednisona Cinfa", "Prednisona"),
    (r"\bparacetamol\s+sun\b", "Paracetamol Sun", "Paracetamol"),
    (r"\bveltassa\b", "Veltassa", "Patiromer"),
    (r"\bhidroferol\b", "Hidroferol", "Calcifediol"),
    (r"\blumigan\b", "Lumigan", "Bimatoprost"),
    (r"\bmastical-d\b", "Mastical-D", "Calcio/colecalciferol"),
    (r"\bomeprazol\s+sandoz(?:\s+farmaceutica)?\b", "Omeprazol Sandoz", "Omeprazol"),
    (r"\badiro\b", "Adiro", "Ácido acetilsalicílico"),
    (r"\bazopt\b", "Azopt", "Brinzolamida"),
    (r"\bbarnix\b", "Barnix", "Barnidipino"),
    (r"\bcarvedilol\s+ratiopharm\b", "Carvedilol ratiopharm", "Carvedilol"),
    (r"\bciclopirox\s+olamina\s+capitec\b", "Ciclopirox olamina Capitec", "Ciclopirox olamina"),
    (r"\bdoxazosina\s+neo\s+vir\b", "Doxazosina Neo Vir", "Doxazosina"),
    (r"\benstilar\b", "Enstilar", "Calcipotriol/Betametasona"),
    (r"\bforxiga\b", "Forxiga", "Dapagliflozina"),
    (r"\bfurosemida\s+uxa\b", "Furosemida Uxa", "Furosemida"),
    (r"\babsorb\s+inc\s+orina\s+dia\b", "Absorb Inc Orina Día", "Absorbente urinario diurno"),
    (r"\babsorb\s+inc\s+orina\s+noc\b", "Absorb Inc Orina Noc", "Absorbente urinario nocturno"),
]
MANUFACTURERS = r"Cinfa|Viatris|Teva|Normon|Alter|Mabo|EFG|Kern Pharma|Mylan|Stada|Sandoz(?: Farmaceutica)?|Tecnigen|Sun|Ratiopharm|Capitec|Uxa|Neo Vir"

# Strengths include denominators (mg/ml, mg/g) and fixed combinations (50mcg/g + 0,5mg/g).
STRENGTH_RE = re.compile(
    r"(?<![\w/])(?P<s>\d+(?:[.,]\d+)?\s*(?:mcg|µg|μg|mg|g|ui)"
    r"(?:\s*/\s*\d+(?:[.,]\d+)?\s*(?:mcg|µg|μg|mg|g|ui))?"
    r"(?:\s*/\s*(?:ml|g|inh|dos|dosis))?"
    r"(?:\s*\+\s*\d+(?:[.,]\d+)?\s*(?:mcg|µg|μg|mg|g|ui)(?:\s*/\s*(?:ml|g))?)?)",
    re.IGNORECASE,
)

DOSE_RE = re.compile(
    r"[-–—]?\s*(?P<amount>\d+(?:[.,]\d+)?)\s*"
    r"(?P<form>amp\s*/\s*vial|amp(?:olla)?(?:s)?|vial(?:es)?|sobre(?:s)?(?:\s+monodosis)?|"
    r"comprim(?:it|ido|idos|s)?|càpsula(?:s)?|capsula(?:s)?|gotes?|gotas?|gota|"
    r"aplicaci[oó](?:n|ó)?|unitats?|unidades?|inhalaci[oó]n(?:es)?|inhalacions?|dosi|dosis)\b"
    r"(?:\s+(?P<descriptor>bebible|bevible))?\s*"
    r"(?:(?P<interval>\d+)\s*(?P<unit>hores?|horas?|dies?|días?)|(?P<according>segons\s+pauta|seg[uú]n\s+pauta))?",
    re.IGNORECASE,
)


def norm(s):
    return re.sub(r"\s+", " ", s.replace("\u00a0", " ").replace(" ", " ")).strip()


def normalize_strength(s):
    s = s.replace("µg", "mcg").replace("μg", "mcg")
    s = re.sub(r"\s*/\s*", "/", s)
    s = re.sub(r"\s*\+\s*", " + ", s)
    s = re.sub(r"\s*(mcg|mg|g)\b", lambda m: m.group(1).lower(), s, flags=re.I)
    s = re.sub(r"\s*(ml|inh)\b", lambda m: m.group(1).lower(), s, flags=re.I)
    return norm(s)


def extract_name_and_strength(raw):
    raw = norm(raw).strip(" -–—")
    sm = STRENGTH_RE.search(raw)
    strength = normalize_strength(sm.group("s")) if sm else ""
    if strength and re.search(r"\binhal", raw, flags=re.I):
        strength = re.sub(r"/inh$", "", strength, flags=re.I)
        strength = re.sub(r"\s*(mcg|mg|g)\b", lambda m: " " + m.group(1).lower(), strength, flags=re.I).strip()
        strength += " inh"
    display_name = None
    ingredient = None
    for pattern, commercial_name, active_ingredient in BRAND_MAP:
        if re.search(pattern, raw, flags=re.I):
            display_name = commercial_name
            ingredient = active_ingredient
            break
    if display_name is None:
        prefix = re.split(rf"\b(?:{MANUFACTURERS})\b", raw, maxsplit=1, flags=re.I)[0]
        if sm:
            prefix = prefix[:sm.start()]
        prefix = re.sub(r"\b\d+\s*$", "", prefix).strip(" -–—")
        display_name = prefix or raw
    display_name = norm(display_name)
    if display_name:
        display_name = display_name[0].upper() + display_name[1:]
    if ingredient:
        # Mostrar marca + principio activo solo cuando la marca sea realmente distinta.
        # Si el nombre ya es el principio activo acompañado del fabricante (p. ej.
        # Atorvastatina Tecnigen o Carvedilol Ratiopharm), mostrar solo el principio activo.
        distinct_brands = {
            "Atrovent", "Foster", "Ozempic", "Synjardy", "Duodart",
            "Veltassa", "Hidroferol", "Lumigan", "Mastical-D", "Adiro",
            "Azopt", "Barnix", "Enstilar", "Forxiga",
        }
        if display_name.casefold() in {b.casefold() for b in distinct_brands}:
            display_name = f"{display_name} ({ingredient})"
        else:
            display_name = ingredient
    return display_name, strength


def spanish_interval(unit, number):
    u = unit.lower()
    if u.startswith(("h", "hora")):
        return "hora" if number == 1 else "horas"
    return "día" if number == 1 else "días"


def make_regimen(amount, form, interval, unit, descriptor):
    amount = amount.replace(",", ".")
    f = form.lower().replace("à", "a")
    desc = (descriptor or "").strip().lower()
    # Preserve non-tablet dosage forms and their original administration units.
    if interval is None:
        if "aplic" in f and ("segons pauta" in desc or "segun pauta" in desc):
            return "1 aplicación según pauta"
        return f"{amount} {form} {desc}".strip() if desc else f"{amount} {form}"
    n = int(interval)
    unit_es = spanish_interval(unit, n)
    is_oral_solid = any(x in f for x in ("comprim", "capsula", "càpsula"))
    if is_oral_solid and unit.lower().startswith(("h", "hora")):
        if n == 24:
            return f"{amount}-0-0"
        if n == 12:
            return f"{amount}-0-{amount}"
        if n == 8:
            return f"{amount}-{amount}-{amount}"
    if "gota" in f or "gote" in f:
        return f"{amount} gota cada {n} {unit_es}"
    if "aplic" in f:
        return f"{amount} aplicación cada {n} {unit_es}"
    if "sobre" in f:
        return f"{amount} sobre cada {n} {unit_es}"
    if "unitat" in f or "unidad" in f:
        return f"{amount} unidad cada {n} {unit_es}" if amount == "1" else f"{amount} unidades cada {n} {unit_es}"
    if "amp" in f or "vial" in f:
        label = "ampolla" if "amp" in f else "vial"
        if desc and desc not in ("bebible", "bevible"):
            label += " " + desc
        elif desc:
            label += " bebible"
        return f"{amount} {label} cada {n} {unit_es}"
    if "inhal" in f:
        return f"{amount} inhalaciones cada {n} {unit_es}"
    return f"{amount} {form} cada {n} {unit_es}"


def parse_records(text):
    text = norm(text)
    date_matches = list(re.finditer(r"\d{2}/\d{2}/\d{4}\s*a\s*\d{2}/\d{2}/\d{4}", text, re.I))
    results = []
    name_cursor = 0
    for idx, dm in enumerate(date_matches):
        name_raw = text[name_cursor:dm.start()].strip(" -–—")
        next_date = date_matches[idx + 1].start() if idx + 1 < len(date_matches) else len(text)
        after = text[dm.end():next_date]
        dose = DOSE_RE.search(after)
        if not dose:
            # Keep the cursor after this date so the next record is not merged into this one.
            name_cursor = dm.end()
            continue
        # Stop the medication name at its own administration instruction.
        active, strength = extract_name_and_strength(name_raw)
        form = dose.group("form")
        descriptor = dose.group("descriptor") or (dose.group("according") or "")
        regimen = make_regimen(dose.group("amount"), form, dose.group("interval"), dose.group("unit"), descriptor)
        display = " ".join(x for x in (active, strength, regimen) if x).strip()
        if display:
            results.append({"display": display})
        name_cursor = dm.end() + dose.end()
    return results


def clear_all():
    # Los callbacks se ejecutan antes de volver a dibujar los widgets.
    # Así se pueden vaciar sus claves sin provocar StreamlitWidgetAlreadyInstantiatedError.
    st.session_state.source_text = ""
    st.session_state.output_text = ""

if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "output_text" not in st.session_state:
    st.session_state.output_text = ""

# Botón LIMPIAR en rojo suave para distinguirlo visualmente.
st.markdown("""
<style>
div.stButton > button[kind="secondary"] {
    border: 1px solid #d9534f;
    color: #b42318;
    background: #fff1f0;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #b42318;
    color: white;
    background: #b42318;
}
</style>
""", unsafe_allow_html=True)

source = st.text_area("Texto de medicación", key="source_text", height=240,
                      placeholder="Pega aquí el texto copiado del tratamiento...")
generate = st.button("Generar pauta", type="primary", use_container_width=True)

if generate:
    records = parse_records(source)
    if not records:
        st.error("No he reconocido medicamentos. Comprueba las fechas y la pauta de cada registro.")
    else:
        st.session_state.output_text = "\n".join(x["display"] for x in records)
        st.success(f"Se han detectado {len(records)} medicamento(s).")

if st.session_state.output_text:
    st.subheader("Resultado")
    st.text_area("Pauta", key="output_text", height=260)
    result_col1, result_col2 = st.columns(2)
    with result_col1:
        # Clipboard access must happen in the user's browser, not on Streamlit's server.
        import json
        safe_output = json.dumps(st.session_state.output_text, ensure_ascii=False)
        components.html(
            f"""<button id="copy-result" style="width:100%;padding:0.5rem 1rem;border:1px solid #999;border-radius:0.5rem;background:white;font-size:16px;cursor:pointer">COPIAR</button>
            <span id="copy-status" style="font:13px sans-serif;margin-left:8px"></span>
            <script>
            const textToCopy = {safe_output};
            document.getElementById('copy-result').addEventListener('click', async () => {{
              const status = document.getElementById('copy-status');
              try {{
                await navigator.clipboard.writeText(textToCopy);
                status.textContent = 'Copiado';
              }} catch (e) {{
                const area = document.createElement('textarea');
                area.value = textToCopy;
                document.body.appendChild(area);
                area.select();
                const ok = document.execCommand('copy');
                area.remove();
                status.textContent = ok ? 'Copiado' : 'Selecciona el texto y copia manualmente';
              }}
            }});
            </script>""",
            height=42,
        )
    with result_col2:
        st.button("LIMPIAR", type="secondary", use_container_width=True,
                  on_click=clear_all)
    st.caption("Los comprimidos y cápsulas se convierten a desayuno-almuerzo-cena cuando la frecuencia lo permite. Otras presentaciones conservan su unidad e intervalo.")
