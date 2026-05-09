"""Git operation tools."""

import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.config import settings
from app.utils.logger import logger
from app.tools.shell_tools import run_command
from app.models.tool_models import CommandResult


async def git_status() -> Optional[CommandResult]:
    """
    Get git status of the workspace.
    
    Returns:
        CommandResult with git status
    """
    return await run_command("git status", cwd=".")


async def git_diff(file_path: Optional[str] = None) -> Optional[CommandResult]:
    """
    Get git diff for files.
    
    Args:
        file_path: Optional specific file to diff
        
    Returns:
        CommandResult with diff output
    """
    command = "git diff"
    if file_path:
        command += f" {file_path}"
    
    return await run_command(command, cwd=".")


async def git_log(max_count: int = 10) -> Optional[CommandResult]:
    """
    Get git commit log.
    
    Args:
        max_count: Maximum number of commits to show
        
    Returns:
        CommandResult with log output
    """
    command = f"git log -n {max_count} --oneline"
    return await run_command(command, cwd=".")


async def git_add(files: Optional[List[str]] = None) -> Optional[CommandResult]:
    """
    Stage files for commit.
    
    Args:
        files: List of files to add, or None for all
        
    Returns:
        CommandResult of git add
    """
    if files:
        command = f"git add {' '.join(files)}"
    else:
        command = "git add ."
    
    return await run_command(command, cwd=".", require_confirmation=False)


async def git_commit(message: str) -> Optional[CommandResult]:
    """
    Create a git commit.
    
    Args:
        message: Commit message
        
    Returns:
        CommandResult of git commit
    """
    # Escape single quotes in message
    safe_message = message.replace("'", "'\\''")
    command = f"git commit -m '{safe_message}'"
    
    return await run_command(command, cwd=".", require_confirmation=False)


async def git_branch(branch_name: Optional[str] = None) -> Optional[CommandResult]:
    """
    List branches or create new branch.
    
    Args:
        branch_name: Optional branch name to create
        
    Returns:
        CommandResult of git branch
    """
    if branch_name:
        command = f"git checkout -b {branch_name}"
    else:
        command = "git branch -a"
    
    return await run_command(command, cwd=".", require_confirmation=False)


async def git_checkout(ref: str) -> Optional[CommandResult]:
    """
    Checkout a branch or commit.
    
    Args:
        ref: Branch name or commit hash
        
    Returns:
        CommandResult of git checkout
    """
    command = f"git checkout {ref}"
    return await run_command(command, cwd=".", require_confirmation=True)


async def git_pull() -> Optional[CommandResult]:
    """
    Pull changes from remote.
    
    Returns:
        CommandResult of git pull
    """
    return await run_command("git pull", cwd=".", require_confirmation=False)


async def git_push(remote: str = "origin", branch: Optional[str] = None) -> Optional[CommandResult]:
    """
    Push changes to remote.
    
    Args:
        remote: Remote name (default: origin)
        branch: Branch to push, or None for current branch
        
    Returns:
        CommandResult of git push
    """
    if branch:
        command = f"git push {remote} {branch}"
    else:
        command = f"git push {remote}"
    
    return await run_command(command, cwd=".", require_confirmation=True)


async def git_get_info() -> Dict[str, Any]:
    """
    Get git repository information.
    
    Returns:
        Dict with git info
    """
    try:
        # Get remote URL
        remote_result = await run_command("git config --get remote.origin.url", cwd=".")
        remote_url = remote_result.stdout.strip() if remote_result else "Unknown"
        
        # Get current branch
        branch_result = await run_command("git rev-parse --abbrev-ref HEAD", cwd=".")
        current_branch = branch_result.stdout.strip() if branch_result else "Unknown"
        
        # Get last commit
        commit_result = await run_command("git rev-parse HEAD", cwd=".")
        last_commit = commit_result.stdout.strip() if commit_result else "Unknown"
        
        return {
            "remote_url": remote_url,
            "current_branch": current_branch,
            "last_commit": last_commit
        }
    except Exception as e:
        logger.error(f"Error getting git info: {e}")
        return {}
