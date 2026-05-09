"""Diff generation and visualization utilities."""

from typing import List, Optional, Dict, Any
from difflib import unified_diff, SequenceMatcher
from pathlib import Path

from app.models.tool_models import FileDiff, DiffChange
from app.utils.logger import logger


def generate_diff(
    old_content: str,
    new_content: str,
    file_path: str
) -> Optional[FileDiff]:
    """
    Generate a diff between two versions of content.
    
    Args:
        old_content: Original content
        new_content: New content
        file_path: File path for reference
        
    Returns:
        FileDiff object or None
    """
    try:
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        changes: List[DiffChange] = []
        additions = 0
        deletions = 0
        
        # Generate unified diff
        diff = unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        
        # Parse diff output
        line_num = 1
        for line in diff:
            if line.startswith('+++') or line.startswith('---'):
                continue
            elif line.startswith('@@ '):
                # Parse line numbers from hunk header
                try:
                    parts = line.split(' ')
                    if len(parts) >= 3:
                        new_range = parts[2].split(',')[0].lstrip('+')
                        line_num = int(new_range) - 1
                except Exception:
                    pass
            elif line.startswith('-'):
                deletions += 1
                changes.append(DiffChange(
                    type="remove",
                    line_number=line_num,
                    old_content=line[1:].rstrip(),
                    new_content=None
                ))
            elif line.startswith('+'):
                additions += 1
                line_num += 1
                changes.append(DiffChange(
                    type="add",
                    line_number=line_num,
                    old_content=None,
                    new_content=line[1:].rstrip()
                ))
            else:
                line_num += 1
        
        return FileDiff(
            file_path=file_path,
            changes=changes,
            additions=additions,
            deletions=deletions
        )
    
    except Exception as e:
        logger.error(f"Error generating diff: {e}")
        return None


def get_diff_stats(diff: FileDiff) -> Dict[str, Any]:
    """
    Get statistics about a diff.
    
    Args:
        diff: FileDiff object
        
    Returns:
        Dict with diff statistics
    """
    return {
        "file_path": diff.file_path,
        "total_changes": len(diff.changes),
        "additions": diff.additions,
        "deletions": diff.deletions,
        "net_change": diff.additions - diff.deletions,
        "modification_percentage": (
            ((diff.additions + diff.deletions) / max(diff.additions + diff.deletions, 1)) * 100
        )
    }


def format_diff_for_display(diff: FileDiff) -> str:
    """
    Format diff for user display.
    
    Args:
        diff: FileDiff object
        
    Returns:
        Formatted diff string
    """
    output = f"--- a/{diff.file_path}\n"
    output += f"+++ b/{diff.file_path}\n"
    output += f"@@ Total changes: +{diff.additions} -{diff.deletions} @@\n\n"
    
    for change in diff.changes:
        if change.type == "add":
            output += f"+ {change.new_content}\n"
        elif change.type == "remove":
            output += f"- {change.old_content}\n"
        else:  # modify
            output += f"- {change.old_content}\n"
            output += f"+ {change.new_content}\n"
    
    return output


def highlight_differences(text1: str, text2: str) -> Dict[str, str]:
    """
    Highlight differences between two strings.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Dict with highlighted versions
    """
    try:
        matcher = SequenceMatcher(None, text1, text2)
        
        highlighted_1 = ""
        highlighted_2 = ""
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                highlighted_1 += text1[i1:i2]
                highlighted_2 += text2[j1:j2]
            elif tag == 'delete':
                highlighted_1 += f"[REMOVED: {text1[i1:i2]}]"
            elif tag == 'insert':
                highlighted_2 += f"[ADDED: {text2[j1:j2]}]"
            elif tag == 'replace':
                highlighted_1 += f"[CHANGED: {text1[i1:i2]}]"
                highlighted_2 += f"[CHANGED: {text2[j1:j2]}]"
        
        return {
            "before": highlighted_1,
            "after": highlighted_2
        }
    
    except Exception as e:
        logger.error(f"Error highlighting differences: {e}")
        return {"before": text1, "after": text2}
