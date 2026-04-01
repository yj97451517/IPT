import os
import sys

def init_dir():
    """初始化文件夹"""
    for d in ["config", "output", "bin"]:
        if not os.path.exists(d):
            os.mkdir(d)

if __name__ == "__main__":
    print("=" * 50)
    print("       IPTV直播源自动筛选工具（影视仓专用）")
    print("=" * 50)
    init_dir()
    from bin.core import run
    run()
    # input("\n按回车退出...")