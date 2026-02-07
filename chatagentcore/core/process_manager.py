import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


class ProcessManager:
    """
    进程管理器 - 用于托管 uos-ai-assistant
    """

    def __init__(self):
        self.command = "uos-ai-assistant"
        self.process: Optional[asyncio.subprocess.Process] = None
        self._should_run = False
        self._monitor_task: Optional[asyncio.Task] = None

    def check_installation(self) -> bool:
        """检查 uos-ai-assistant 是否已安装"""
        path = shutil.which(self.command)
        if not path:
            logger.error(f"未找到 {self.command}。请确保 uos-ai 已正确安装。")
            return False
        logger.info(f"检测到 {self.command} 安装路径: {path}")
        return True

    def is_already_running(self) -> bool:
        """检查 uos-ai-assistant 是否已经在运行"""
        try:
            # 1. 粗略获取所有相关 PID
            cmd = ["pgrep", "-f", self.command]
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                pids = result.stdout.decode().strip().split()
                my_pid = os.getpid()
                
                real_instances = []
                for pid in pids:
                    if int(pid) == my_pid:
                        continue
                        
                    # 2. 精确验证：检查 /proc/<pid>/exe 是否以 uos-ai-assistant 结尾
                    # 这能完美排除 tail, grep, vim 等误报
                    try:
                        exe_link = os.readlink(f"/proc/{pid}/exe")
                        if exe_link.endswith(f"/{self.command}"):
                            real_instances.append(pid)
                    except (ProcessLookupError, FileNotFoundError, OSError):
                        continue
                
                if real_instances:
                    logger.error(f"{self.command} 已经在运行 (PIDs: {', '.join(real_instances)})，请先关闭它。")
                    return True
                    
        except Exception as e:
            logger.warning(f"检查进程状态时出错: {e}")
        return False

    async def start(self) -> bool:
        """启动 Agent 进程"""
        # 1. 检查安装
        if not self.check_installation():
            return False

        # 2. 检查是否已运行
        if self.is_already_running():
            return False

        if self.process and self.process.returncode is None:
            logger.warning("Agent process is already running in this session")
            return True

        self._should_run = True
        success = await self._spawn_process()
        
        if success:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
        return success

    async def stop(self):
        """停止 Agent 进程"""
        self._should_run = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self.process and self.process.returncode is None:
            logger.info(f"正在停止 {self.command} (PID: {self.process.pid})...")
            try:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"{self.command} 未能优雅停止，强制结束...")
                    self.process.kill()
                    await self.process.wait()
            except Exception as e:
                logger.error(f"停止进程时出错: {e}")
        
        self.process = None

    async def _spawn_process(self) -> bool:
        """执行具体的进程拉起"""
        logger.info(f"正在启动: {self.command}")
        
        try:
            # 修复 PyInstaller 打包环境下 LD_LIBRARY_PATH 污染导致子进程 crash 的问题
            env = os.environ.copy()
            if getattr(sys, 'frozen', False):
                if 'LD_LIBRARY_PATH_ORIG' in env:
                    env['LD_LIBRARY_PATH'] = env['LD_LIBRARY_PATH_ORIG']
                else:
                    env.pop('LD_LIBRARY_PATH', None)

            self.process = await asyncio.create_subprocess_exec(
                self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None,
                env=env
            )
            
            logger.info(f"{self.command} 启动成功 (PID: {self.process.pid})")
            
            asyncio.create_task(self._read_stream(self.process.stdout, "AGENT-STDOUT"))
            asyncio.create_task(self._read_stream(self.process.stderr, "AGENT-STDERR"))
            
            return True
        except Exception as e:
            logger.error(f"拉起 {self.command} 失败: {e}")
            return False

    async def _read_stream(self, stream, prefix: str):
        if not stream:
            return
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                logger.debug(f"[{prefix}] {line.decode().strip()}")
        except Exception as e:
            logger.error(f"读取 {prefix} 时出错: {e}")

    async def _monitor_loop(self):
        while self._should_run:
            if self.process:
                if self.process.returncode is not None:
                    ret_code = self.process.returncode
                    if ret_code == 0:
                        logger.warning(f"{self.command} 已通过退出码 0 正常退出。停止托管。")
                        self._should_run = False
                        break

                    logger.warning(f"{self.command} 意外退出，退出码: {ret_code}")
                    if self._should_run:
                        logger.info("正在尝试重新启动...")
                        await asyncio.sleep(5.0)
                        if self._should_run:
                            await self._spawn_process()
                    else:
                        break
            
            await asyncio.sleep(2.0)


_process_manager: Optional[ProcessManager] = None

def get_process_manager() -> ProcessManager:
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager