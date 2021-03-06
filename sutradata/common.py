from difflib import SequenceMatcher
import re, json
import urllib.request
import traceback

from sutradata.models import *
from tasks.models import *

SEPARATORS_PATTERN = re.compile('[pb\n]')
CID_FORMAT = '%sv%03dp%04d0%02dn%02d'

def get_accurate_cut(text1, text2, cut_json, pid):
    """
    用于文字校对后的文本比对，text1是文字校对审定后得到的精确本，text2是OCR原始结果，都包含换行和换页标记。
    """
    cut = json.loads(cut_json)
    old_char_lst = cut['char_data']
    old_char_lst_length = len(old_char_lst)
    for char_data in old_char_lst:
        char_data['line_no'] = int(char_data['line_no']) #int(char_data['char_id'][18:20])
        char_data['char_no'] = int(char_data['char_no']) #int(char_data['char_id'][21:23])

    char_lst = []

    line_no = 1
    char_no = 1
    char_index = 0 # 下一个从old_char_lst要取出的字
    char_lst_length = 0
    opcodes = SequenceMatcher(None, text1, text2, False).get_opcodes()
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            i = i1
            while i < i2:
                if text1[i] == '\n':
                    line_no += 1
                    char_no = 1
                else:
                    char_data = old_char_lst[char_index]
                    char_data['line_no'] = line_no
                    char_data['char_no'] = char_no
                    char_lst.append(char_data)
                    char_no += 1
                    char_lst_length += 1
                    char_index += 1
                i += 1
        elif tag == 'insert': # OCR本多出的字，需删除
            # text2[j1:j2]
            # 将相邻的同样的字标记为"need_confirm"
            # TODO: 改进
            length = j2 - j1
            # 前length
            i = 1
            temp_char_index = char_lst_length - 1
            while text2[j1-length*i : j2-length*i] == text2[j1:j2]:
                # 处理前length个字
                j = j2 - 1
                while temp_char_index >= 0 and j >= j1:
                    if text2[j] != '\n':
                        char_lst[temp_char_index]['need_confirm'] = 1
                        temp_char_index -= 1
                    j -= 1
                i += 1
            # 后length
            i = 1
            temp_char_index = char_index
            while text2[j1+length*i : j2+length*i] == text2[j1:j2]:
                # 处理后length个字
                j = j1
                while j < j2 and temp_char_index < old_char_lst_length:
                    if text2[j] != '\n':
                        old_char_lst[temp_char_index]['need_confirm'] = 1
                        temp_char_index += 1
                    j += 1
                i += 1

            for ch in text2[j1:j2]:
                if ch != '\n':
                    char_index += 1
        elif tag == 'replace':
            i = i1
            j = j1
            while i < i2:
                ch = text1[i]
                if ch == '\n':
                    line_no += 1
                    char_no = 1
                else:
                    if (i-i1)+j1 < j2:
                        #print('char_index: ', char_index)
                        char_data = old_char_lst[char_index]
                        char_index += 1
                        char_data['line_no'] = line_no
                        char_data['char_no'] = char_no
                        char_data['ch'] = ch
                        char_data['old_ch'] = text2[(i-i1)+j1]
                    else:
                        char_data = {
                            'line_no': line_no,
                            'char_no': char_no,
                            'ch': ch,
                            'added': 1,
                        }
                    char_lst.append(char_data)
                    char_no += 1
                i += 1
        elif tag == 'delete': # OCR本缺少的字，需要增加
            add_count = i2 -i1
            for i in range(add_count):
                ch = text1[i1 + i]
                if ch == '\n':
                    line_no += 1
                    char_no = 1
                else:
                    char_data = {
                        'line_no': line_no,
                        'char_no': char_no,
                        'ch': ch,
                        'added': 1,
                    }
                    char_lst.append(char_data)
                    char_no += 1

    # 给增加的字加上切分坐标
    line_count = 0
    char_map = {}
    line_char_count = {}
    for char_data in char_lst:
        line_no = char_data['line_no']
        char_no = char_data['char_no']
        line_char_str = '%02dn%02d' % (line_no, char_no)
        cid = '%s%s' % (pid, line_char_str)
        #char_data['char_id'] = cid
        if 'char_id' in char_data:
            del char_data['char_id']
        char_map[line_char_str] = char_data
        if line_no in line_char_count:
            line_char_count[line_no] += 1
        else:
            line_char_count[line_no] = 1
        if line_no > line_count:
            line_count = line_no

    add_count = 0
    wrong_count = 0
    confirm_count = 0
    for char_data in char_lst:
        if 'old_char' in char_data:
            wrong_count += 1
        elif 'need_confirm' in char_data:
            confirm_count += 1
        elif 'added' in char_data:
            try:
                line_no = char_data['line_no']
                char_no = char_data['char_no']
                prev_line_no = line_no - 1
                next_line_no = line_no + 1
                cur_line_char_count = line_char_count[line_no]
                s = None
                if line_char_count.get(prev_line_no, 0) == cur_line_char_count:
                    s = '%02dn%02d' % (prev_line_no, char_no)
                elif line_char_count.get(next_line_no, 0) == cur_line_char_count:
                    s = '%02dn%02d' % (next_line_no, char_no)
                if not s:
                    if prev_line_no > 0:
                        s = '%02dn%02d' % (prev_line_no, char_no)
                    else:
                        s = '%02dn%02d' % (next_line_no, char_no)
                char_data['y'] = char_map[s]['y']
                char_data['h'] = char_map[s]['h']

                if char_no == 1:
                    s = '%02dn%02d' % (line_no, char_no + 1)
                else:
                    s = '%02dn%02d' % (line_no, char_no - 1)
                if s in char_map and 'x' in char_map[s]:
                    char_data['x'] = char_map[s]['x']
                    char_data['w'] = char_map[s]['w']
                else:
                    s1 = '%02dn%02d' % (line_no - 1, char_no)
                    s2 = '%02dn%02d' % (line_no + 1, char_no)
                    if (s1 in char_map) and (s2 in char_map):
                        if char_map[s1]['x'] - char_map[s2]['x'] < 200:
                            char_data['x'] = (char_map[s1]['x'] + char_map[s2]['x'])/2
                            char_data['w'] = (char_map[s1]['w'] + char_map[s2]['w'])/2
                        elif line_no <= (line_count/2):
                            char_data['x'] = char_map[s1]['x']
                            char_data['w'] = char_map[s1]['w']
                        else:
                            char_data['x'] = char_map[s2]['x']
                            char_data['w'] = char_map[s2]['w']
                    elif (s1 in char_map):
                        char_data['x'] = char_map[s1]['x']
                        char_data['w'] = char_map[s1]['w']
                    elif (s2 in char_map):
                        char_data['x'] = char_map[s2]['x']
                        char_data['w'] = char_map[s2]['w']
                    else:
                        print('no adjacent line:', char_data)
            except:
                print('get_accurate_cut except: ', json.dumps(char_data))

    # 得到字框顶点中最小和最大的x, y
    min_x = 10000
    min_y = 10000
    max_x = 0
    max_y = 0
    for char_data in char_lst:
        x = char_data.get('x', None)
        y = char_data.get('y', None)
        w = char_data.get('w', 0)
        h = char_data.get('h', 0)
        if x and y:
            if x < min_x:
                min_x = x
            if (x + w) > max_x:
                max_x = x + w
            if y < min_y:
                min_y = y
            if (y + h) > max_y:
                max_y = y + h
    return char_lst, add_count, wrong_count, confirm_count, min_x, min_y, max_x, max_y
    
def fetch_cut_file(reel, vol_page):
    cut_url = '%s%s%s.cut' % (settings.IMAGE_URL_PREFIX, reel.url_prefix(), vol_page)
    with urllib.request.urlopen(cut_url) as f:
        print('fetch done: %s, page: %s' % (reel, vol_page))
        data = f.read()
        return data

def compute_accurate_cut(reel):
    sid = reel.sutra.sid
    pagetexts = reel.text[2:].split('\np\n')
    reel_correct_texts = list(ReelCorrectText.objects.filter(reel=reel).order_by('-id')[0:1])
    if not reel_correct_texts:
        return None
    reel_correct_text = reel_correct_texts[0]
    correct_pagetexts = reel_correct_text.text[2:].split('\np\n')
    print('page_count: ', len(pagetexts), len(correct_pagetexts))
    page_count = len(pagetexts)
    correct_page_count = len(correct_pagetexts)
    for i in range(page_count):
        page_no = i + 1
        vol_page = reel.start_vol_page + i
        pid = '%s%03d%02d' % (sid, reel.reel_no, page_no)
        cut_file = fetch_cut_file(reel, vol_page)
        if i < correct_page_count:
            char_lst, cut_add_count, cut_wrong_count, cut_confirm_count, min_x, min_y, max_x, max_y = get_accurate_cut(correct_pagetexts[i], pagetexts[i], cut_file, pid)
            cut_verify_count = cut_add_count + cut_wrong_count + cut_confirm_count
            cut_info = {
                'page_code': pid,
                'reel_no': '%sr%03d' % (sid, reel.reel_no),
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y,
                'char_data': char_lst,
            }
            cut_info_json = json.dumps(cut_info, indent=None)
            page = Page(pid=pid, reel_id=reel.id, reel_page_no=i+1, vol_no=reel.start_vol, page_no=page_no,
            text=correct_pagetexts[i], cut_info=cut_info_json, cut_updated_at=timezone.now(),
            cut_add_count=cut_add_count, cut_wrong_count=cut_wrong_count, cut_confirm_count=cut_confirm_count,
            cut_verify_count=cut_verify_count)
        else:
            cut_info = {
                'page_code': pid,
                'reel_no': '%sr%03d' % (sid, reel.reel_no),
                'char_data': [],
            }
            cut_info_json = json.dumps(cut_info, indent=None)
            page = Page(pid=pid, reel_id=reel.id, reel_page_no=i+1, vol_no=reel.start_vol, page_no=page_no,
            text='', cut_info=cut_info_json, cut_updated_at=timezone.now())
        page.save()

SUTRA_CLEAN_PATTERN = re.compile('[「」　 \r]')
def clean_sutra_text(text):
    text = text.replace('\r\n', '\n').replace('\n\n', '\n')
    return SUTRA_CLEAN_PATTERN.sub('', text)

PUNCT_CHARACTERS = '：，。；、\n'
def extract_punct(text):
    pos = 0
    punct_lst = []
    text_lst = []
    for ch in text:
        if ch in PUNCT_CHARACTERS:
            punct_lst.append( (pos, ch) )
        else:
            text_lst.append(ch)
            pos += 1
    return (punct_lst, ''.join(text_lst))

def judge_merge_text_punct(text, punct_lst):
    i = 0
    punct_idx = 0
    text_length = len(text)
    punct_lst_length = len(punct_lst)
    result_lst = []
    line = []
    while i < text_length and punct_idx < punct_lst_length:
        if punct_lst[punct_idx][0] <= i:
            s = punct_lst[punct_idx][1]
            if s == '\n':
                result_lst.append(''.join(line))
                line = []
            else:
                line.append(s)
            punct_idx += 1
        elif punct_lst[punct_idx][0] > i:
            line.append(text[i])
            i += 1
    return result_lst

def extract_page_line_separators(text):
    if text == '':
        return []
    pages = text.split('\np\n')
    if pages[0].startswith('p\n'): # 去掉最前面的p
        pages[0] = pages[0][2:]
    separators = []
    pos = 0
    page_index = 0
    page_count = len(pages)
    while page_index < page_count:
        lines = pages[page_index].split('\n')
        line_cnt = len(lines)
        i = 0
        while i < line_cnt:
            pos += len(lines[i])
            if i == (line_cnt - 1): # 一页中最后一行
                if page_index != (page_count - 1): # 非最后一页
                    separators.append( (pos, 'p') )
            else:
                separators.append( (pos, '\n') )
            i += 1
        page_index += 1
    return separators

class ReelText(object):
    def __init__(self, reel, text, tripitaka_id, sid, vol_no, start_vol_page, separators_json=None):
        self.reel = reel
        self.text = SEPARATORS_PATTERN.sub('', text)
        self.tripitaka_id = tripitaka_id
        self.tripitaka = Tripitaka.objects.get(id=tripitaka_id)
        self.sid = sid
        self.vol_no = vol_no
        self.start_vol_page = start_vol_page
        if separators_json:
            self.separators = json.loads(separators_json)
        else:
            self.separators = extract_page_line_separators(text)

    def get_cid_range(self, start_index, end_index): # del
        if self.tripitaka.code == 'CB':
            return ('', '')
        count_p = 0
        count_n = 0
        start_cid = ''
        start_page_no = -1
        start_line_no = -1
        start_char_no = -1
        end_page_no = -1
        end_line_no = -1
        end_char_no = -1
        last_pos = 0
        separator_count = len(self.separators)
        i = 0
        while i <= separator_count:
            if i < separator_count:
                pos, separator = self.separators[i]
            else:
                pos = len(self.text)
            if pos > start_index and start_char_no == -1:
                # 第一次pos > start_index时
                start_page_no = count_p + 1
                start_line_no = count_n + 1
                start_char_no = start_index - last_pos + 1
            if pos > end_index and end_char_no == -1:
                # 第一次pos > end_index时
                end_page_no = count_p + 1
                end_line_no = count_n + 1
                end_char_no = end_index - last_pos + 1

            if i == separator_count:
                break
            if separator == 'p':
                count_p += 1
                count_n = 0
            elif separator == '\n':
                count_n += 1            
            last_pos = pos
            i += 1
        start_page = self.start_vol_page + start_page_no - 1
        end_page = self.start_vol_page + end_page_no - 1
        start_cid = CID_FORMAT % (self.sid, self.vol_no, start_page, start_line_no, start_char_no)
        end_cid = CID_FORMAT % (self.sid, self.vol_no, end_page, end_line_no, end_char_no)
        return (start_cid, end_cid)

    def get_char_position(self, start_index, end_index):
        count_p = 0
        count_n = 0
        start_page_no = -1
        start_line_no = -1
        start_char_no = -1
        end_page_no = -1
        end_line_no = -1
        end_char_no = -1
        last_pos = 0
        separator_count = len(self.separators)
        i = 0
        while i <= separator_count:
            if i < separator_count:
                pos, separator = self.separators[i]
            else:
                pos = len(self.text)
            if pos > start_index and start_char_no == -1:
                # 第一次pos > start_index时
                start_page_no = count_p + 1
                start_line_no = count_n + 1
                start_char_no = start_index - last_pos + 1
            if pos > end_index and end_char_no == -1:
                # 第一次pos > end_index时
                end_page_no = count_p + 1
                end_line_no = count_n + 1
                end_char_no = end_index - last_pos + 1

            if i == separator_count:
                break
            if separator == 'p':
                count_p += 1
                count_n = 0
            elif separator == '\n':
                count_n += 1            
            last_pos = pos
            i += 1
        return (start_page_no, start_line_no, start_char_no, end_page_no, end_line_no, end_char_no)

def get_reel_text(reel):
    pages = []
    for vol_page in range(reel.start_vol_page, reel.end_vol_page+1):
        data = fetch_cut_file(reel, vol_page)
        if not data:
            return ''
        json_data = json.loads(data)
        chars = ['p\n']
        last_line_no = 1
        last_char_no = 0
        for char_data in json_data['char_data']:
            line_no = int(char_data['line_no'])
            char_no = int(char_data['char_no'])
            if line_no != last_line_no:
                chars.append('\n')
                last_char_no = 0
            if char_no != last_char_no + 1:
                print('%s char_no error: ' % reel, reel.reel_no, vol_page, line_no, char_no)
                return ''
            chars.append(char_data['ch'])
            last_line_no = line_no
            last_char_no = char_no
        pages.append( ''.join(chars) )
    return '\n'.join(pages)