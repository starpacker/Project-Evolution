#!/usr/bin/env python3
"""
Evolution Logo Display
一个有趣的ASCII艺术logo展示脚本
"""

import time
import sys
import os

# 颜色代码
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 亮色
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # 背景色
    BG_BLACK = '\033[40m'
    BG_BLUE = '\033[44m'
    BG_CYAN = '\033[46m'

# Evolution Logo - DNA螺旋 + 大脑 + 进化主题
LOGO_FRAMES = [
    # Frame 1 - DNA螺旋开始形成
    f"""
{Colors.BRIGHT_CYAN}        ╔═══════════════════════════════════════════════════╗
        ║                                                   ║
        ║     {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}                                      ║
        ║    {Colors.BRIGHT_MAGENTA}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_YELLOW}╲{Colors.BRIGHT_CYAN}     {Colors.BRIGHT_WHITE}███████╗██╗   ██╗ ██████╗ {Colors.BRIGHT_CYAN}    ║
        ║   {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_WHITE}██╔════╝██║   ██║██╔═══██╗{Colors.BRIGHT_CYAN}   ║
        ║    {Colors.BRIGHT_YELLOW}╲{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_MAGENTA}╱{Colors.BRIGHT_CYAN}     {Colors.BRIGHT_WHITE}█████╗  ██║   ██║██║   ██║{Colors.BRIGHT_CYAN}   ║
        ║     {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_WHITE}██╔══╝  ╚██╗ ██╔╝██║   ██║{Colors.BRIGHT_CYAN}   ║
        ║    {Colors.BRIGHT_YELLOW}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_MAGENTA}╲{Colors.BRIGHT_CYAN}     {Colors.BRIGHT_WHITE}███████╗ ╚████╔╝ ╚██████╔╝{Colors.BRIGHT_CYAN}   ║
        ║   {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_WHITE}╚══════╝  ╚═══╝   ╚═════╝ {Colors.BRIGHT_CYAN}   ║
        ║                                                   ║
        ║         {Colors.BRIGHT_GREEN}🧬 Your 7×24 AI Companion 🧠{Colors.BRIGHT_CYAN}          ║
        ║                                                   ║
        ╚═══════════════════════════════════════════════════╝{Colors.RESET}
    """,
    
    # Frame 2 - DNA螺旋旋转
    f"""
{Colors.BRIGHT_CYAN}        ╔═══════════════════════════════════════════════════╗
        ║                                                   ║
        ║      {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}                                     ║
        ║     {Colors.BRIGHT_YELLOW}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_MAGENTA}╲{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_WHITE}███████╗██╗   ██╗ ██████╗ {Colors.BRIGHT_CYAN}    ║
        ║    {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}   {Colors.BRIGHT_WHITE}██╔════╝██║   ██║██╔═══██╗{Colors.BRIGHT_CYAN}   ║
        ║     {Colors.BRIGHT_MAGENTA}╲{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_YELLOW}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_WHITE}█████╗  ██║   ██║██║   ██║{Colors.BRIGHT_CYAN}   ║
        ║      {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}     {Colors.BRIGHT_WHITE}██╔══╝  ╚██╗ ██╔╝██║   ██║{Colors.BRIGHT_CYAN}   ║
        ║     {Colors.BRIGHT_MAGENTA}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_YELLOW}╲{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_WHITE}███████╗ ╚████╔╝ ╚██████╔╝{Colors.BRIGHT_CYAN}   ║
        ║    {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}   {Colors.BRIGHT_WHITE}╚══════╝  ╚═══╝   ╚═════╝ {Colors.BRIGHT_CYAN}   ║
        ║                                                   ║
        ║         {Colors.BRIGHT_GREEN}🧬 Your 7×24 AI Companion 🧠{Colors.BRIGHT_CYAN}          ║
        ║                                                   ║
        ╚═══════════════════════════════════════════════════╝{Colors.RESET}
    """,
    
    # Frame 3 - 完整展示
    f"""
{Colors.BRIGHT_CYAN}        ╔═══════════════════════════════════════════════════╗
        ║                                                   ║
        ║     {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}                                      ║
        ║    {Colors.BRIGHT_MAGENTA}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_YELLOW}╲{Colors.BRIGHT_CYAN}     {Colors.BRIGHT_WHITE}███████╗██╗   ██╗ ██████╗ {Colors.BRIGHT_CYAN}    ║
        ║   {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_WHITE}██╔════╝██║   ██║██╔═══██╗{Colors.BRIGHT_CYAN}   ║
        ║    {Colors.BRIGHT_YELLOW}╲{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_MAGENTA}╱{Colors.BRIGHT_CYAN}     {Colors.BRIGHT_WHITE}█████╗  ██║   ██║██║   ██║{Colors.BRIGHT_CYAN}   ║
        ║     {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_WHITE}██╔══╝  ╚██╗ ██╔╝██║   ██║{Colors.BRIGHT_CYAN}   ║
        ║    {Colors.BRIGHT_YELLOW}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_MAGENTA}╲{Colors.BRIGHT_CYAN}     {Colors.BRIGHT_WHITE}███████╗ ╚████╔╝ ╚██████╔╝{Colors.BRIGHT_CYAN}   ║
        ║   {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_WHITE}╚══════╝  ╚═══╝   ╚═════╝ {Colors.BRIGHT_CYAN}   ║
        ║                                                   ║
        ║         {Colors.BRIGHT_GREEN}🧬 Your 7×24 AI Companion 🧠{Colors.BRIGHT_CYAN}          ║
        ║                                                   ║
        ╚═══════════════════════════════════════════════════╝{Colors.RESET}
    """
]

# 静态完整Logo
STATIC_LOGO = f"""
{Colors.BRIGHT_CYAN}╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}                                            ║
║       {Colors.BRIGHT_MAGENTA}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_YELLOW}╲{Colors.BRIGHT_CYAN}        {Colors.BRIGHT_WHITE}███████╗██╗   ██╗ ██████╗ {Colors.BRIGHT_CYAN}       ║
║      {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}       {Colors.BRIGHT_WHITE}██╔════╝██║   ██║██╔═══██╗{Colors.BRIGHT_CYAN}       ║
║       {Colors.BRIGHT_YELLOW}╲{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_MAGENTA}╱{Colors.BRIGHT_CYAN}        {Colors.BRIGHT_WHITE}█████╗  ██║   ██║██║   ██║{Colors.BRIGHT_CYAN}       ║
║        {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}         {Colors.BRIGHT_WHITE}██╔══╝  ╚██╗ ██╔╝██║   ██║{Colors.BRIGHT_CYAN}       ║
║       {Colors.BRIGHT_YELLOW}╱{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_MAGENTA}╲{Colors.BRIGHT_CYAN}        {Colors.BRIGHT_WHITE}███████╗ ╚████╔╝ ╚██████╔╝{Colors.BRIGHT_CYAN}       ║
║      {Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}      {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}       {Colors.BRIGHT_WHITE}╚══════╝  ╚═══╝   ╚═════╝ {Colors.BRIGHT_CYAN}       ║
║       {Colors.BRIGHT_MAGENTA}╲{Colors.BRIGHT_CYAN}    {Colors.BRIGHT_YELLOW}╱{Colors.BRIGHT_CYAN}                                           ║
║        {Colors.BRIGHT_MAGENTA}●{Colors.BRIGHT_CYAN}━━{Colors.BRIGHT_YELLOW}●{Colors.BRIGHT_CYAN}                                            ║
║                                                           ║
║            {Colors.BRIGHT_GREEN}🧬 Your 7×24 AI Companion 🧠{Colors.BRIGHT_CYAN}              ║
║                                                           ║
║  {Colors.BRIGHT_YELLOW}Roles:{Colors.RESET} {Colors.WHITE}Secretary │ Mentor │ Trainer │ Emotional │ Intel{Colors.BRIGHT_CYAN} ║
║  {Colors.BRIGHT_YELLOW}Version:{Colors.RESET} {Colors.WHITE}0.1.0{Colors.BRIGHT_CYAN}                    {Colors.BRIGHT_YELLOW}Status:{Colors.RESET} {Colors.BRIGHT_GREEN}●{Colors.WHITE} Ready{Colors.BRIGHT_CYAN}     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
"""

def clear_screen():
    """清屏"""
    os.system('clear' if os.name != 'nt' else 'cls')

def animate_logo(cycles=2):
    """动画展示logo"""
    try:
        for _ in range(cycles):
            for frame in LOGO_FRAMES:
                clear_screen()
                print(frame)
                time.sleep(0.3)
    except KeyboardInterrupt:
        pass

def show_static_logo():
    """显示静态logo"""
    clear_screen()
    print(STATIC_LOGO)

def typewriter_effect(text, delay=0.03):
    """打字机效果"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def show_startup_sequence():
    """启动序列动画"""
    clear_screen()
    
    # 动画logo
    animate_logo(cycles=1)
    
    # 显示静态logo
    show_static_logo()
    
    print()
    
    # 启动信息
    startup_messages = [
        f"{Colors.BRIGHT_CYAN}[{Colors.BRIGHT_GREEN}✓{Colors.BRIGHT_CYAN}] Initializing Evolution AI Agent...{Colors.RESET}",
        f"{Colors.BRIGHT_CYAN}[{Colors.BRIGHT_GREEN}✓{Colors.BRIGHT_CYAN}] Loading memory systems...{Colors.RESET}",
        f"{Colors.BRIGHT_CYAN}[{Colors.BRIGHT_GREEN}✓{Colors.BRIGHT_CYAN}] Connecting to knowledge base...{Colors.RESET}",
        f"{Colors.BRIGHT_CYAN}[{Colors.BRIGHT_GREEN}✓{Colors.BRIGHT_CYAN}] Activating 5 core roles...{Colors.RESET}",
        f"{Colors.BRIGHT_CYAN}[{Colors.BRIGHT_GREEN}✓{Colors.BRIGHT_CYAN}] System ready!{Colors.RESET}",
    ]
    
    for msg in startup_messages:
        typewriter_effect(msg, delay=0.02)
        time.sleep(0.3)
    
    print()
    print(f"{Colors.BRIGHT_YELLOW}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.BRIGHT_WHITE}  Evolution is now running and ready to assist you.{Colors.RESET}")
    print(f"{Colors.BRIGHT_WHITE}  Type your message or press Ctrl+C to exit.{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}{'─' * 60}{Colors.RESET}")
    print()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Evolution Logo Display')
    parser.add_argument('--static', action='store_true', help='Show static logo only')
    parser.add_argument('--animate', action='store_true', help='Show animation only')
    parser.add_argument('--startup', action='store_true', help='Show full startup sequence')
    
    args = parser.parse_args()
    
    try:
        if args.static:
            show_static_logo()
        elif args.animate:
            animate_logo(cycles=3)
            show_static_logo()
        elif args.startup:
            show_startup_sequence()
        else:
            # 默认：完整启动序列
            show_startup_sequence()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BRIGHT_CYAN}Evolution logo display terminated.{Colors.RESET}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
