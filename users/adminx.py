import xadmin
from sutradata.models import LQSutra
class LQSutraAdmin(object):
    list_display = ['sid','name','total_reels'] #自定义显示这两个字段  
    
xadmin.site.register(LQSutra,LQSutraAdmin)#注册