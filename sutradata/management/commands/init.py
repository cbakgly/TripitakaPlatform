from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from sutradata.models import *
from tasks.models import *
from sutradata.common import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback

import re, json

class Command(BaseCommand):
    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        try:
            admin = User.objects.get(username='admin')
        except:
            admin = User.objects.create_superuser('admin', 'admin@example.com', 'longquan')

        try:
            lqsutra = LQSutra.objects.get(sid='LQ003100') #大方廣佛華嚴經60卷
        except:
            # create LQSutra
            lqsutra = LQSutra(sid='LQ003100', name='大方廣佛華嚴經', total_reels=60)
            lqsutra.save()

        # create Sutra
        # Sutra.objects.all().delete()
        YB = Tripitaka.objects.get(code='YB')
        try:
            huayan_yb = Sutra.objects.get(sid='YB000860')
        except:
            huayan_yb = Sutra(sid='YB000860', tripitaka=YB, code='00086', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_yb.save()

        # 永乐北藏第1卷的文本
        try:
            huayan_yb_1 = Reel.objects.get(sutra=huayan_yb, reel_no=1)
        except:
            huayan_yb_1 = Reel(sutra=huayan_yb, reel_no=1, start_vol=27,
            start_vol_page=1, end_vol=27, end_vol_page=23, edition_type=Reel.EDITION_TYPE_CHECKED,
            path1='27')
            text = get_reel_text(huayan_yb_1)
            #filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001.txt' % huayan_yb.sid)
            #with open(filename, 'r') as f:
            #    huayan_yb_1.text = f.read()
            huayan_yb_1.text = text
            huayan_yb_1.save()

        filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001_fixed.txt' % huayan_yb.sid)
        with open(filename, 'r') as f:
            text = f.read()
            ReelCorrectText(reel=huayan_yb_1, text=text).save()

        # # 得到精确的切分数据
        # try:
        #     compute_accurate_cut(huayan_yb_1)
        # except Exception:
        #     traceback.print_exc()

        # 高丽第1卷
        GL = Tripitaka.objects.get(code='GL')
        try:
            huayan_gl = Sutra.objects.get(sid='GL000800')
        except:
            huayan_gl = Sutra(sid='GL000800', tripitaka=GL, code='00080', variant_code='0',
            name='大方廣佛華嚴經', lqsutra=lqsutra, total_reels=60)
            huayan_gl.save()
        try:
            huayan_gl_1 = Reel.objects.get(sutra=huayan_gl, reel_no=1)
        except:
            huayan_gl_1 = Reel(sutra=huayan_gl, reel_no=1, start_vol=14,
            start_vol_page=31, end_vol=14, end_vol_page=37, edition_type=Reel.EDITION_TYPE_CHECKED,
            path1='80', path2='1')
            filename = os.path.join(BASE_DIR, 'data/sutra_text/%s_001.txt' % huayan_gl.sid)
            with open(filename, 'r') as f:
                text = f.read()
                huayan_gl_1.text = text
                huayan_gl_1.save()
                reelcorrecttext = ReelCorrectText(reel=huayan_gl_1, text=text)
                reelcorrecttext.save()

        # create BatchTask
        BatchTask.objects.all().delete()
        priority = 2
        CORRECT_TIMES = 2
        CORRECT_VERIFY_TIMES = 1
        JUDGE_TIMES = 2
        JUDGE_VERIFY_TIMES = 1
        batch_task = BatchTask(priority=priority, publisher=admin)
        batch_task.save()

        # create Tasks
        # Correct Task
        separators = extract_page_line_separators(huayan_yb_1.text)
        separators_json = json.dumps(separators, separators=(',', ':'))

        # 文字校对
        diff_lst, base_text = CompareReel.generate_compare_reel(reelcorrecttext.text, huayan_yb_1.text)
        compare_reel = CompareReel(reel=huayan_yb_1, base_reel=huayan_gl_1, base_text=base_text)
        compare_reel.save()

        task1 = Task(id=1, batch_task=batch_task, typ=Task.TYPE_CORRECT, base_reel=huayan_gl_1, task_no=1, status=Task.STATUS_READY,
        publisher=admin)
        task1.compare_reel = compare_reel
        task1.separators = separators_json
        task1.reel = huayan_yb_1
        task1.save()

        task2 = Task(id=2, batch_task=batch_task, typ=Task.TYPE_CORRECT, base_reel=huayan_gl_1, task_no=2, status=Task.STATUS_READY,
        publisher=admin)
        task2.compare_reel = compare_reel
        task2.separators = separators_json
        task2.reel = huayan_yb_1
        #task2.base_reel = huayan_gl_1
        task2.save()

        task3 = Task(id=3, batch_task=batch_task, typ=Task.TYPE_CORRECT_VERIFY, base_reel=huayan_gl_1, task_no=0, status=Task.STATUS_NOT_READY,
        publisher=admin)
        task3.compare_reel = compare_reel
        #task3.separators = separators_json
        task3.reel = huayan_yb_1
        task3.save()
        
        compare_segs = []
        correct_segs_lst = []
        for tag, base_pos, pos, base_text, ocr_text in diff_lst:
            compare_seg = CompareSeg(compare_reel=compare_reel,
            base_pos=base_pos,
            ocr_text=ocr_text, base_text=base_text)
            compare_segs.append(compare_seg)
            correct_segs = []
            correct_seg = CorrectSeg(task=task1)
            correct_seg.selected_text = compare_seg.ocr_text
            correct_seg.position = pos
            correct_segs.append(correct_seg)
            correct_seg = CorrectSeg(task=task2)
            correct_seg.selected_text = compare_seg.ocr_text
            correct_seg.position = pos
            correct_segs.append(correct_seg)
            correct_segs_lst.append(correct_segs)
        CompareSeg.objects.bulk_create(compare_segs)
        correct_seg_lst = []
        for i in range(len(compare_segs)):
            for correct_seg in correct_segs_lst[i]:
                correct_seg.compare_seg = compare_segs[i]
                correct_seg_lst.append(correct_seg)
        CorrectSeg.objects.bulk_create(correct_seg_lst)



