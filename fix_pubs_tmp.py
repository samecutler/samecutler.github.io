#!/usr/bin/env python3
import os, re, sys
PUB_DIR = '/sessions/rcw-01mxwbzmkqaalwyytujjq7xn/mnt/website/content/publication'
SUP_MAP = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻','n':'ⁿ','i':'ⁱ','a':'ᵃ','b':'ᵇ','c':'ᶜ','d':'ᵈ','e':'ᵉ','f':'ᶠ','g':'ᵍ','h':'ʰ','j':'ʲ','k':'ᵏ','l':'ˡ','m':'ᵐ','o':'ᵒ','p':'ᵖ','r':'ʳ','s':'ˢ','t':'ᵗ','u':'ᵘ','v':'ᵛ','w':'ʷ','x':'ˣ','y':'ʸ','z':'ᶻ'}
SUB_MAP = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉','+':'₊','-':'₋','e':'ₑ','a':'ₐ','o':'ₒ','x':'ₓ','i':'ᵢ'}
CMD_SYM = {'sim':'~','lesssim':'≲','gtrsim':'≳','leq':'≤','geq':'≥','gg':'≫','ll':'≪','approx':'≈','pm':'±','mp':'∓','times':'×','cdot':'·','cdots':'⋯','propto':'∝','infty':'∞','odot':'☉','star':'★','langle':'⟨','rangle':'⟩','alpha':'α','beta':'β','gamma':'γ','delta':'δ','epsilon':'ε','varepsilon':'ε','zeta':'ζ','eta':'η','theta':'θ','vartheta':'θ','iota':'ι','kappa':'κ','lambda':'λ','mu':'μ','nu':'ν','xi':'ξ','pi':'π','varpi':'π','rho':'ρ','varrho':'ρ','sigma':'σ','varsigma':'ς','tau':'τ','upsilon':'υ','phi':'φ','varphi':'φ','chi':'χ','psi':'ψ','omega':'ω','Delta':'Δ','Gamma':'Γ','Theta':'Θ','Lambda':'Λ','Xi':'Ξ','Pi':'Π','Sigma':'Σ','Upsilon':'Υ','Phi':'Φ','Psi':'Ψ','Omega':'Ω','AA':'Å','textemdash':'—','textendash':'–','textasciitilde':'~','textdegree':'°','textmu':'μ','texttimes':'×','log':'log','ln':'ln','exp':'exp'}
CMD_PASSTHRU = {'mathrm','mathbf','mathit','mathsf','mathtt','mathcal','mathbb','text','textrm','textsf','textit','textbf','textsc','texttt','mbox','hbox','rm','bf','it','emph','underline'}

def apply_syms_simple(s):
    for cmd, sym in sorted(CMD_SYM.items(), key=lambda x: -len(x[0])):
        s = re.sub(r'\\' + re.escape(cmd) + r'(?=[^a-zA-Z]|$)', sym, s)
    s = re.sub(r'\{?\\ensuremath\{([^}]+)\}\}?', lambda m: CMD_SYM.get(m.group(1).strip(), m.group(1).strip()), s)
    return s

def do_sub(inner):
    inner = inner.strip()
    inner = apply_syms_simple(inner)
    if all(c in SUB_MAP for c in inner):
        return ''.join(SUB_MAP[c] for c in inner)
    return inner

def do_sup(inner):
    inner = inner.strip()
    inner = apply_syms_simple(inner)
    inner = re.sub(r'\{?\\ensuremath\{([^}]+)\}\}?', lambda m: CMD_SYM.get(m.group(1).strip(), m.group(1).strip()), inner)
    inner = inner.strip('{}')
    if all(c in SUP_MAP for c in inner):
        return ''.join(SUP_MAP[c] for c in inner)
    return inner

def process_math(expr):
    s = expr.strip()
    s = s.replace('PLACEHOLDERlambda', 'λ').replace('PLACEHOLDERrho', 'ρ').replace('PLACEHOLDERsim', '~')
    s = re.sub(r'\{\\ensuremath\{([^}]+)\}\}', lambda m: CMD_SYM.get(m.group(1).strip(), m.group(1).strip()), s)
    s = re.sub(r'\\(?:mathrm|mathbf|mathit|mathsf|mathtt|mathcal|mathbb|text|textrm|rm|boldsymbol)\{([^}]*)\}', r'\1', s)
    for cmd, sym in sorted(CMD_SYM.items(), key=lambda x: -len(x[0])):
        s = re.sub(r'\\' + re.escape(cmd) + r'(?=[^a-zA-Z]|$)', sym, s)
    s = s.replace('\u2500', '–').replace('\u2012', '-').replace('\u2013', '-').replace('\u2014', '-')
    def sub_repl(m):
        inner = m.group(1) if m.group(1) is not None else m.group(2)
        return do_sub(inner)
    s = re.sub(r'_\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|_([A-Za-z0-9★☉*])', sub_repl, s)
    def sup_repl(m):
        inner = m.group(1) if m.group(1) is not None else m.group(2)
        return do_sup(inner)
    s = re.sub(r'\^\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|\^([A-Za-z0-9★☉+\-*])', sup_repl, s)
    for _ in range(5):
        ns = re.sub(r'\{([^{}]*)\}', r'\1', s)
        if ns == s: break
        s = ns
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'\\[a-zA-Z]+\*?\s*', '', s)
    s = re.sub(r'\\[^a-zA-Z\s]', '', s)
    return s.strip()

def bib_abstract_to_markdown(raw):
    s = raw
    s = s.replace('PLACEHOLDERlambda', 'λ').replace('PLACEHOLDERrho', 'ρ').replace('PLACEHOLDERsim', '~')
    s = re.sub(r'[ \t]*\n[ \t]*', ' ', s)
    s = re.sub(r'  +', ' ', s)
    s = s.replace("``", '\u201c').replace("''", '\u201d').replace("`", '\u2018')
    s = s.replace('{\\textemdash}', '—').replace('\\textemdash', '—')
    s = s.replace('{\\textendash}', '–').replace('\\textendash', '–')
    s = s.replace('---', '—').replace('--', '–')
    s = s.replace('\u2500', '–').replace('\u2012', '-')
    def repl_em(m):
        inner = m.group(1).strip()
        return CMD_SYM.get(inner, process_math(inner))
    s = re.sub(r'\{\\ensuremath\{([^}]+)\}\}', repl_em, s)
    s = re.sub(r'\\ensuremath\{([^}]+)\}', repl_em, s)
    s = re.sub(r'\\raisebox\{[^}]*\}\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\raisebox\{[^}]*\}', '', s)
    s = re.sub(r'\\textbackslash([a-zA-Z]+)\\textbackslash', r'\\\1', s)
    s = re.sub(r'\\textbackslash([a-zA-Z]+)', r'\\\1', s)
    s = s.replace('\\textbackslash', '\\')
    ring_map = {'A':'Å','a':'å','U':'Ů','u':'ů'}
    s = re.sub(r'\\r\{([A-Za-z])\}', lambda m: ring_map.get(m.group(1), m.group(1)), s)
    s = s.replace('\\textasciitilde', '~').replace('\\textdegree', '°').replace('\\textmu', 'μ').replace('\\texttimes', '×')
    s = re.sub(r'\\AA\b', 'Å', s)
    s = re.sub(r'\\AA\{\}', 'Å', s)
    for cmd, sym in sorted(CMD_SYM.items(), key=lambda x: -len(x[0])):
        if cmd in ('log', 'ln', 'exp', 'S', 'AA'):
            continue
        s = re.sub(r'\\' + re.escape(cmd) + r'(?=[^a-zA-Z]|$)', sym, s)
    def repl_dollar(m):
        return process_math(m.group(1))
    s = re.sub(r'\$\$(.+?)\$\$', repl_dollar, s, flags=re.DOTALL)
    s = re.sub(r'\$(.+?)\$', repl_dollar, s, flags=re.DOTALL)
    s = re.sub(r'\\log\b', 'log', s)
    s = re.sub(r'\\ln\b', 'ln', s)
    for cmd in CMD_PASSTHRU:
        s = re.sub(r'\\' + re.escape(cmd) + r'\{([^{}]*)\}', r'\1', s)
    for _ in range(6):
        ns = re.sub(r'\{([^{}]*)\}', r'\1', s)
        if ns == s: break
        s = ns
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'\\[a-zA-Z]+\*?\s*', '', s)
    s = re.sub(r'\\[^a-zA-Z\s]', '', s)
    s = re.sub(r'\s*–\s*', '–', s)
    s = re.sub(r'\s*—\s*', '—', s)
    s = re.sub(r'  +', ' ', s)
    return s.strip()

def get_bib_field(bib, field):
    m = re.search(r'(?<!\w)' + re.escape(field) + r'\s*=\s*', bib, re.IGNORECASE)
    if not m:
        return None
    pos = m.end()
    if pos >= len(bib):
        return None
    ch = bib[pos]
    if ch == '"':
        i = pos + 1
        depth = 0
        buf = []
        while i < len(bib):
            c = bib[i]
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            elif c == '"' and depth == 0:
                break
            buf.append(c)
            i += 1
        val = ''.join(buf).strip()
        if val.startswith('{') and val.endswith('}'):
            val = val[1:-1]
        return val
    elif ch == '{':
        depth = 0
        for i, c in enumerate(bib[pos:]):
            if c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return bib[pos+1:pos+i].strip()
    else:
        m2 = re.match(r'([^\s,}]+)', bib[pos:])
        if m2:
            return m2.group(1).rstrip(',')
    return None

def update_index_md(idx_path, abstract_md, adsurl, featured):
    with open(idx_path, 'r', encoding='utf-8') as f:
        content = f.read()
    abstract_yaml = abstract_md.replace("'", "''")
    new_content = re.sub(r"^abstract: '.*?'$", lambda _: f"abstract: '{abstract_yaml}'", content, flags=re.MULTILINE | re.DOTALL)
    if adsurl and 'name: ADS' not in new_content:
        def add_ads(m):
            links_block = m.group(0)
            ads_entry = f"- name: ADS\n  url: {adsurl}\n"
            return re.sub(r'^(links:\n)', r'\1' + ads_entry, links_block, count=1, flags=re.MULTILINE)
        new_content = re.sub(r'^links:.*?(?=^\w|\Z)', add_ads, new_content, flags=re.MULTILINE | re.DOTALL)
    if featured:
        new_content = re.sub(r"(focal_point:\s*)['\"]?[^'\"\n]*['\"]?", r"\1Smart", new_content)
    if new_content != content:
        with open(idx_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    slugs = sorted(os.listdir(PUB_DIR))
    updated = 0
    skipped = 0
    errors = []
    for slug in slugs:
        cite_path = os.path.join(PUB_DIR, slug, 'cite.bib')
        idx_path  = os.path.join(PUB_DIR, slug, 'index.md')
        if not os.path.isfile(cite_path) or not os.path.isfile(idx_path):
            continue
        bib = open(cite_path, encoding='utf-8').read()
        abstract_raw = get_bib_field(bib, 'abstract')
        adsurl = get_bib_field(bib, 'adsurl')
        if adsurl:
            adsurl = adsurl.strip()
        if not abstract_raw:
            print(f"  {slug}: no abstract in cite.bib")
            skipped += 1
            continue
        try:
            abstract_md = bib_abstract_to_markdown(abstract_raw)
        except Exception as e:
            errors.append(f"{slug}: {e}")
            skipped += 1
            continue
        idx_content = open(idx_path, encoding='utf-8').read()
        featured = bool(re.search(r'^featured:\s*true', idx_content, re.MULTILINE))
        try:
            changed = update_index_md(idx_path, abstract_md, adsurl, featured)
            if changed:
                updated += 1
                print(f"  + {slug}" + (" [featured]" if featured else ""))
            else:
                skipped += 1
                print(f"  - {slug} (no change)")
        except Exception as e:
            errors.append(f"{slug}: {e}")
            skipped += 1
    print(f"\nDone: {updated} updated, {skipped} skipped")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e}")

if __name__ == '__main__':
    main()
