import pandas as pd
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Excelファイルから相性値データを読み込み
try:
    df_main_comp = pd.read_excel('compatibility_table.xlsx', index_col=0)
    df_sub_comp = pd.read_excel('compatibility_sub_table.xlsx', index_col=0)
except FileNotFoundError as e:
    print(f"Error: {e.filename}が見つかりません。")
    print("このファイルには、既存モンスター間の相性値を格納してください。")
    exit()

# シンボルと合計相性値の範囲
symbol_ranges = {
    '☆': (615, float('inf')),
    '◎': (496, 614),
    '○': (375, 495),
    '△': (258, 374),
    '×': (0, 257)
}

# 既知の相性値を取得するヘルパー関数（主血統用）
def get_known_comp(vertical, horizontal):
    try:
        if vertical == '新モンスター' or horizontal == '新モンスター':
            return None
        return df_main_comp.loc[vertical, horizontal]
    except KeyError:
        return None

# 副血統相性値を取得するヘルパー関数
def get_sub_comp(vertical_sub, horizontal_sub):
    if vertical_sub == '新モンスター' or horizontal_sub == '新モンスター':
        return None
    
    vertical_is_rare_bloodline = vertical_sub == 'レア'
    horizontal_is_rare_bloodline = horizontal_sub == 'レア'
    
    if vertical_is_rare_bloodline and horizontal_is_rare_bloodline:
        return 32
    elif vertical_is_rare_bloodline and not horizontal_is_rare_bloodline:
        return 16
    elif not vertical_is_rare_bloodline and horizontal_is_rare_bloodline:
        return 32
    else:
        try:
            return df_sub_comp.loc[vertical_sub, horizontal_sub]
        except KeyError:
            return None

# 相性値計算API
@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    
    ch, f, ff, fm = data['ch'], data['f'], data['ff'], data['fm']
    m, mf, mm = data['m'], data['mf'], data['mm']
    
    ch_sub, f_sub, ff_sub, fm_sub = data['ch_sub'], data['f_sub'], data['ff_sub'], data['fm_sub']
    m_sub, mf_sub, mm_sub = data['m_sub'], data['mf_sub'], data['mm_sub']
    
    af = data['af']
    
    known_main_sum = 0
    known_sub_sum = 0
    all_known = True

    # 主血統の合計を計算
    terms_main = [
        get_known_comp(ch, f),
        get_known_comp(ch, m),
        get_known_comp(f, m),
        min(get_known_comp(ch, ff), get_known_comp(f, ff)) if get_known_comp(ch, ff) is not None and get_known_comp(f, ff) is not None else None,
        min(get_known_comp(ch, fm), get_known_comp(f, fm)) if get_known_comp(ch, fm) is not None and get_known_comp(f, fm) is not None else None,
        min(get_known_comp(ch, mf), get_known_comp(m, mf)) if get_known_comp(ch, mf) is not None and get_known_comp(m, mf) is not None else None,
        min(get_known_comp(ch, mm), get_known_comp(m, mm)) if get_known_comp(ch, mm) is not None and get_known_comp(m, mm) is not None else None,
    ]

    for val in terms_main:
        if val is not None:
            known_main_sum += val
        else:
            all_known = False

    # 副血統の合計を計算
    terms_sub = [
        get_sub_comp(ch_sub, f_sub),
        get_sub_comp(ch_sub, m_sub),
        get_sub_comp(f_sub, m_sub),
        min(get_sub_comp(ch_sub, ff_sub), get_sub_comp(f_sub, ff_sub)) if get_sub_comp(ch_sub, ff_sub) is not None and get_sub_comp(f_sub, ff_sub) is not None else None,
        min(get_sub_comp(ch_sub, fm_sub), get_sub_comp(f_sub, fm_sub)) if get_sub_comp(ch_sub, fm_sub) is not None and get_sub_comp(f_sub, fm_sub) is not None else None,
        min(get_sub_comp(ch_sub, mf_sub), get_sub_comp(m_sub, mf_sub)) if get_sub_comp(ch_sub, mf_sub) is not None and get_sub_comp(m_sub, mf_sub) is not None else None,
        min(get_sub_comp(ch_sub, mm_sub), get_sub_comp(m_sub, mm_sub)) if get_sub_comp(ch_sub, mm_sub) is not None and get_sub_comp(m_sub, mm_sub) is not None else None,
    ]
    
    for val in terms_sub:
        if val is not None:
            known_sub_sum += val
        else:
            all_known = False
    
    known_sum = known_main_sum + known_sub_sum + af
    
    return jsonify({
        'known_sum': known_sum,
        'all_known': all_known
    })

# HTMLテンプレートのルート
@app.route('/')
def index():
    all_monsters = df_main_comp.index.tolist()
    all_monsters.append('新モンスター')
    all_monsters.append('レア')
    monster_rarity = {m: m in ['Phoenix', 'Mocchi'] for m in all_monsters}
    return render_template('index.html', all_monsters=all_monsters, symbol_ranges=symbol_ranges, monster_rarity=monster_rarity)

if __name__ == '__main__':
    app.run(debug=True)