'use client';

import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import CodeMirror from '@uiw/react-codemirror';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';
import { xcodeLight } from '@uiw/codemirror-theme-xcode';
import { EditorView } from '@codemirror/view';
import { useTheme } from 'next-themes';
import {
  getGithubFileContent,
  commitGithubFile,
  GitHubCommitRequest,
} from '@/lib/api';
import { Button } from '@/components/ui/button';

interface GitHubCodeViewerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  owner: string;
  repo: string;
  path: string;
  branch?: string;
}

export function GitHubCodeViewer({
  open,
  onOpenChange,
  owner,
  repo,
  path,
  branch = 'main',
}: GitHubCodeViewerProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (open) {
      getGithubFileContent(owner, repo, path, branch)
        .then((text) => setContent(text))
        .catch((err) => console.error('Failed to load file', err));
    }
  }, [open, owner, repo, path, branch]);

  const handleSave = async () => {
    const payload: GitHubCommitRequest = {
      path,
      content,
      message: `Update ${path}`,
      branch,
    };
    setSaving(true);
    try {
      await commitGithubFile(owner, repo, payload);
      // eslint-disable-next-line no-console
      console.log('File committed');
    } catch (err) {
      console.error('Failed to commit file', err);
    } finally {
      setSaving(false);
    }
  };

  const theme = mounted && resolvedTheme === 'dark' ? vscodeDark : xcodeLight;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-[900px]">
        <DialogHeader>
          <DialogTitle>{owner}/{repo}/{path}</DialogTitle>
        </DialogHeader>
        <div className="h-[70vh]">
          <CodeMirror
            value={content}
            theme={theme}
            onChange={(v) => setContent(v)}
            basicSetup={{ lineNumbers: true }}
            extensions={[EditorView.lineWrapping]}
            className="h-full"
          />
        </div>
        <div className="flex justify-end pt-2">
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
