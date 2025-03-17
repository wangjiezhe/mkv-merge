import os
from ctypes import CDLL, CFUNCTYPE, c_byte, c_char_p
from json import dumps, loads

libpath = os.path.join(os.path.dirname(__file__), "mkvlib.so")
lib = CDLL(libpath)


def _lcb(lcb):
    @CFUNCTYPE(None, c_byte, c_char_p)
    def logcallback(l, s):  # noqa: E741
        if lcb:
            lcb(l, s.decode())

    return logcallback


def version():
    """
    获取库版本信息。

    Returns:
        str: 库版本信息。
    """
    call = lib.Version
    call.restype = c_char_p
    return call().decode()


def initInstance(lcb):
    """
    初始化实例。

    Args:
        lcb (function): 日志回调函数，原型为 void (*logCallback)(unsigned char l, char* str)。
                        l: 日志等级(0:Info, 1:Warning, 2:SWarning, 3:Error, 4:Progress)
                        str: UTF-8编码的字符串。
    """
    call = lib.InitInstance
    call(_lcb(lcb))


def getMKVInfo(file):
    """
    查询一个mkv文件内封的字幕和字体信息。

    Args:
        file (str): mkv文件路径。

    Returns:
        dict: json格式的字体信息，如果出错会返回"null"。
    """
    call = lib.GetMKVInfo
    call.restype = c_char_p
    return loads(call(file.encode()).decode())


def dumpMKV(file, output, subset, lcb):
    """
    抽取一个mkv文件里的字幕和字体并顺便进行子集化(可选)。

    Args:
        file (str): mkv文件路径。
        output (str): 输出文件夹路径。
        subset (bool): 是否进行子集化。
        lcb (function): 日志回调函数。

    Returns:
        bool: 是否全程无错。
    """
    call = lib.DumpMKV
    return call(file.encode(), output.encode(), subset, _lcb(lcb))


def checkSubset(file, lcb):
    """
    查询一个mkv文件是否需要子集化操作。

    Args:
        file (str): mkv文件路径。
        lcb (function): 日志回调函数。

    Returns:
        dict: 包含是否已子集化和是否出错两个bool成员的json文本。
    """
    call = lib.CheckSubset
    call.restype = c_char_p
    return loads(call(file.encode(), _lcb(lcb)).decode())


def createMKV(file, tracks, attachments, output, slang, stitle, clean, lcb):
    """
    将字幕和字体封进mkv文件。

    Args:
        file (str): 源文件路径(并非一定要是mkv文件,其他视频文件也可.)。
        tracks (list): 字幕文件路径数组。
        attachments (list): 字体文件路径数组。
        output (str): 输出文件路径。
        slang (str): 默认字幕语言。
        stitle (str): 默认字幕标题。
        clean (bool): 是否清除源mkv原有的字幕和字体。
        lcb (function): 日志回调函数。

    Returns:
        bool: 是否全程无错。
    """
    call = lib.CreateMKV
    _tracks = dumps(tracks)
    _attachments = dumps(attachments)
    return call(
        file.encode(),
        _tracks.encode(),
        _attachments.encode(),
        output.encode(),
        slang.encode(),
        stitle.encode(),
        clean,
        _lcb(lcb),
    )


def assFontSubset(files, fonts, output, dirSafe, lcb):
    """
    对字幕和字体进行子集化操作。

    Args:
        files (list): 字幕文件路径数组。
        fonts (str): 字体文件夹路径。
        output (str): 成品输出文件夹路径。
        dirSafe (bool): 是否把成品输出到"${output}/subsetted"文件夹里(为了安全建议设置为true)。
        lcb (function): 日志回调函数。

    Returns:
        bool: 是否全程无错。
    """
    call = lib.ASSFontSubset
    _files = dumps(files)
    return call(_files.encode(), fonts.encode(), output.encode(), dirSafe, _lcb(lcb))


def queryFolder(dir, lcb):
    """
    查询一个文件夹里的mkv文件是否需要子集化。

    Args:
        dir (str): 文件夹路径。
        lcb (function): 日志回调函数。

    Returns:
        list: 需要子集化的mkv文件路径数组。
    """
    call = lib.QueryFolder
    call.restype = c_char_p
    return call(dir.encode(), _lcb(lcb))


def dumpMKVs(dir, output, subset, lcb):
    """
    抽取一个文件夹里的mkv的字幕和字体并顺便进行子集化(可选)。

    Args:
        dir (str): 文件夹路径。
        output (str): 输出文件夹路径。
        subset (bool): 是否进行子集化。
        lcb (function): 日志回调函数。

    Returns:
        bool: 是否全程无错。
    """
    call = lib.DumpMKVs
    return call(dir.encode(), output.encode(), subset, _lcb(lcb))


def createMKVs(vDir, sDir, fDir, tDir, oDir, slang, stitle, clean, lcb):
    """
    从一组文件夹获得情报自动生成一组mkv并自动进行子集化操作。

    Args:
        vDir (str): 视频文件夹路径。
        sDir (str): 字幕文件夹路径。
        fDir (str): 字体文件夹路径。
        tDir (str): 子集化数据临时存放文件夹路径(如果为空字符串则自动指定到系统临时文件夹如"/tmp")。
        oDir (str): 成品输出文件夹路径。
        slang (str): 默认字幕语言。
        stitle (str): 默认字幕标题。
        clean (bool): 是否清除源mkv原有的字幕和字体。
        lcb (function): 日志回调函数。

    Returns:
        bool: 是否全程无错。
    """
    call = lib.CreateMKVs
    return call(
        vDir.encode(),
        sDir.encode(),
        fDir.encode(),
        tDir.encode(),
        oDir.encode(),
        slang.encode(),
        stitle.encode(),
        clean,
        _lcb(lcb),
    )


def makeMKVs(dir, data, output, slang, stitle, subset, lcb):
    """
    用子集化后的数据目录替代原有的字幕和字体。

    Args:
        dir (str): 源mkv集合文件夹路径。
        data (str): 子集化后的数据文件夹路径。
        output (str): 新mkv集合输出文件夹路径。
        slang (str): 默认字幕语言。
        stitle (str): 默认字幕标题。
        subset (bool): 是否进行子集化。
        lcb (function): 日志回调函数。

    Returns:
        bool: 是否全程无错。
    """
    call = lib.MakeMKVs
    return call(
        dir.encode(),
        data.encode(),
        output.encode(),
        slang.encode(),
        stitle.encode(),
        subset,
        _lcb(lcb),
    )


def createBlankOrBurnVideo(t, s, enc, ass, fontdir, output):
    """
    创建一个空视频或者烧录字幕的视频。

    Args:
        t (str): 视频时长
        s (str): 源视频路径(留空即生成空视频)。
        enc (str): 视频编码器。
        ass (str): 字幕文件路径(当s为空时,t参数自动设置为字幕时长)。
        fontdir (str): 字体目录路径。
        output (str): 输出文件。

    Returns:
        bool: 是否成功完成
    """
    call = lib.CreateBlankOrBurnVideo
    call(
        t.encode(),
        s.encode(),
        enc.encode(),
        ass.encode(),
        fontdir.encode(),
        output.encode(),
    )


def createTestVideo(asses, s, fontdir, enc, burn, lcb):
    """
    创建测试视频。

    Args:
        asses (list): 字幕文件数组的json格式文本。
        s (str): 源视频路径。
        fontdir (str): 字体目录路径。
        enc (str): 视频编码器。
        burn (bool): 是否烧录字幕。
        lcb (function): 日志回调函数。

    Returns:
        bool: 是否成功完成。
    """
    call = lib.CreateTestVideo
    _files = dumps(asses)
    call(_files.encode(), s.encode(), fontdir.encode(), enc.encode(), burn, _lcb(lcb))


def ass2pgs(asses, resolution, frameRate, fontdir, output):
    """
    ASS转PGS。

    Args:
        asses (list): 字幕文件数组的json格式文本。
        resolution (str): PGS分辨率(如"1920x1080","HD"等)。
        frameRate (str): PGS帧率(如"23.976","30000/1001"等)。
        fontdir (str): 字体目录路径。
        output (str): 输出目录。

    Returns:
        bool: 是否成功完成。
    """
    call = lib.Ass2Pgs()
    _files = dumps(asses)
    call(
        _files.encode(),
        resolution.encode(),
        frameRate.encode(),
        fontdir.encode(),
        output.encode(),
    )


def a2p(en, apc, pr, pf):
    """
    启用ass转pgs(应在执行工作流之前调用)。

    Args:
        en (bool): 是否启用ass转pgs。
        apc (bool): 是否使ass与pgs共存。
        pr (str): pgs分辨率。
        pf (str): pgs帧率。
    """
    call = lib.A2P
    call(en, apc, pr.encode(), pf.encode())


def getFontsList(files, fonts, lcb):
    """
    取得数组内字幕需要的全部字体,如果设置了Check则会试图匹配字体,并输出匹配失败的列表.。

    Args:
        files (list): 字幕文件路径的json的数组。
        fonts (str): 字体文件夹路径。
        lcb (function): 日志回调函数。

    Returns:
        dict: json格式的二维数组(第一个成员是需要的字体名称,第二个成员是没有匹配成功的字体名称.)。
    """
    call = lib.GetFontsList
    call.restype = c_char_p
    _files = dumps(files)
    return loads(call(_files.encode(), fonts.encode(), _lcb(lcb)).decode())


def cache(ccs):
    """
    设置字体缓存(应在执行工作流之前调用)。

    Args:
        ccs (list): 包含缓存文件路径数组的json格式文本。
    """
    call = lib.Cache
    _ccs = dumps(ccs)
    call(_ccs.encode())


def getFontInfo(p):
    """
    查询一个字体的信息。

    Args:
        p (str): 字体文件路径。

    Returns:
        dict: json格式的文件信息,如果出错会返回"null"。
    """
    call = lib.GetFontInfo
    call.restype = c_char_p
    return loads(call(p.encode()).decode())


def createFontsCache(dir, output, lcb):
    """
    从字体目录创建缓存。

    Args:
        dir (str): 字体文件目录。
        output (str): 缓存文件保存路径。
        lcb (function): 日志回调函数。

    Returns:
        list: 缓存失败字体的json格式的数组。
    """
    call = lib.CreateFontsCache
    call.restype = c_char_p
    return loads(call(dir.encode(), output.encode(), _lcb(lcb)).decode())


def copyFontsFromCache(asses, dist, lcb):
    """
    从缓存复制字幕所需的字体。

    Args:
        asses (list): 字幕文件路径的json的数组。
        dist (str): 字体文件保存目录。
        lcb (function): 日志回调函数。

    Returns:
        bool: 是否全部导出。
    """
    call = lib.CopyFontsFromCache
    _files = dumps(asses)
    return call(_files.encode(), dist.encode(), _lcb(lcb))


def mks(en):
    """
    使用mks输出。

    Args:
        en (bool): 是否启用。
    """
    call = lib.MKS
    call(en)


def nrename(n):
    """
    子集化时不重命名字体。

    Args:
        n (bool): 是否不重命名。
    """
    call = lib.NRename
    call(n)


def noverwrite(n):
    """
    输出时是否跳过已存在的文件

    Args:
      n (bool): 是否跳过
    """
    call = lib.NOverwrite
    call(n)


def check(c, s):
    """
    启用检查模式(影响包含子集化操作的工作流)。

    Args:
        c (bool): 是否启用检查模式。
        s (bool): 是否启用严格模式。
    """
    call = lib.Check
    call(c, s)
