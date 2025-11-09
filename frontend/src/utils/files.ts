/**
 * File utilities for type detection, size formatting, and MIME type mapping.
 */

/**
 * Get MIME type from file extension or filename.
 */
export function getMimeType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';

  const mimeTypes: Record<string, string> = {
    // Text
    txt: 'text/plain',
    md: 'text/markdown',
    json: 'application/json',
    xml: 'application/xml',
    html: 'text/html',
    css: 'text/css',
    js: 'application/javascript',
    ts: 'application/typescript',
    py: 'text/plain',
    sh: 'text/x-shellscript',
    yml: 'application/x-yaml',
    yaml: 'application/x-yaml',

    // Images
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    png: 'image/png',
    gif: 'image/gif',
    svg: 'image/svg+xml',
    webp: 'image/webp',
    ico: 'image/x-icon',

    // Audio
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
    flac: 'audio/flac',
    m4a: 'audio/mp4',

    // Video
    mp4: 'video/mp4',
    webm: 'video/webm',
    mov: 'video/quicktime',
    mkv: 'video/x-matroska',

    // Archives
    zip: 'application/zip',
    tar: 'application/x-tar',
    gz: 'application/gzip',
    rar: 'application/x-rar-compressed',
    '7z': 'application/x-7z-compressed',

    // Documents
    pdf: 'application/pdf',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ppt: 'application/vnd.ms-powerpoint',
    pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  };

  return mimeTypes[ext] || 'application/octet-stream';
}

/**
 * Get file category from MIME type.
 */
export function getFileCategory(mimeType: string): 'image' | 'audio' | 'video' | 'text' | 'archive' | 'document' | 'other' {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType.startsWith('audio/')) return 'audio';
  if (mimeType.startsWith('video/')) return 'video';
  if (mimeType.startsWith('text/') || mimeType === 'application/json') return 'text';
  if (mimeType.includes('zip') || mimeType.includes('tar') || mimeType.includes('rar') || mimeType.includes('7z')) return 'archive';
  if (mimeType.includes('pdf') || mimeType.includes('word') || mimeType.includes('excel') || mimeType.includes('powerpoint')) return 'document';
  return 'other';
}

/**
 * Check if file is viewable in browser.
 */
export function isViewable(mimeType: string): boolean {
  const category = getFileCategory(mimeType);
  return ['image', 'text', 'audio', 'video'].includes(category);
}

/**
 * Check if file is editable as text.
 */
export function isEditable(mimeType: string): boolean {
  return mimeType.startsWith('text/') ||
    mimeType === 'application/json' ||
    mimeType === 'application/xml' ||
    mimeType === 'application/javascript' ||
    mimeType === 'application/typescript';
}

/**
 * Format file size in bytes to human-readable format.
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format file permissions from octal mode.
 */
export function formatPermissions(mode: number): string {
  const octal = (mode & parseInt('777', 8)).toString(8);
  return octal.padStart(3, '0');
}

/**
 * Parse octal permissions to rwx format.
 */
export function permissionsToRwx(mode: number): string {
  const octal = (mode & parseInt('777', 8)).toString(8).padStart(3, '0');
  let rwx = '';

  const digits = octal.split('');
  const triplets = ['owner', 'group', 'other'];
  const result: string[] = [];

  digits.forEach((digit, i) => {
    const num = parseInt(digit, 8);
    let perm = '';
    perm += (num & 4) ? 'r' : '-';
    perm += (num & 2) ? 'w' : '-';
    perm += (num & 1) ? 'x' : '-';
    result.push(perm);
  });

  return result.join(' ');
}

/**
 * Get file icon class based on file type.
 */
export function getFileIcon(filename: string, type: string): string {
  if (type === 'directory') return '📁';
  if (type === 'symlink') return '🔗';

  const mimeType = getMimeType(filename);
  const category = getFileCategory(mimeType);

  const icons: Record<string, string> = {
    image: '🖼️',
    audio: '🎵',
    video: '🎬',
    text: '📄',
    archive: '📦',
    document: '📋',
    other: '📄',
  };

  return icons[category] || '📄';
}

/**
 * Get file extension from filename.
 */
export function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || '';
}

/**
 * Get filename without extension.
 */
export function getFileNameWithoutExtension(filename: string): string {
  const lastDotIndex = filename.lastIndexOf('.');
  if (lastDotIndex === -1) return filename;
  return filename.substring(0, lastDotIndex);
}

/**
 * Get directory name from path.
 */
export function getDirName(path: string): string {
  return path.split('/').filter(Boolean).pop() || '/';
}

/**
 * Get parent directory from path.
 */
export function getParentDir(path: string): string {
  if (path === '/' || path === '.') return path;
  const parts = path.split('/').filter(Boolean);
  parts.pop();
  return parts.length ? '/' + parts.join('/') : '/';
}

/**
 * Join path segments.
 */
export function joinPath(...parts: string[]): string {
  return parts
    .join('/')
    .split('/')
    .filter((p) => p && p !== '.')
    .join('/') || '/';
}

/**
 * Normalize path.
 */
export function normalizePath(path: string): string {
  if (!path.startsWith('/')) {
    path = '/' + path;
  }
  return path.replace(/\/+/g, '/');
}

/**
 * Check if filename matches search query.
 */
export function matchesSearch(filename: string, query: string): boolean {
  return filename.toLowerCase().includes(query.toLowerCase());
}

/**
 * Format modification time.
 */
export function formatModifiedTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleString();
  } catch {
    return isoString;
  }
}

/**
 * Get file size limits for validation (in MB).
 */
export const FILE_SIZE_LIMITS = {
  UPLOAD: 500, // 500 MB upload limit
  VIEW: 10,    // 10 MB for inline viewing
  EDIT: 5,     // 5 MB for editing
};

/**
 * Check if file size is within upload limit.
 */
export function isValidUploadSize(bytes: number): boolean {
  return bytes <= FILE_SIZE_LIMITS.UPLOAD * 1024 * 1024;
}

/**
 * Check if file can be viewed inline.
 */
export function canViewInline(bytes: number, mimeType: string): boolean {
  return isViewable(mimeType) && bytes <= FILE_SIZE_LIMITS.VIEW * 1024 * 1024;
}

/**
 * Check if file can be edited.
 */
export function canEdit(bytes: number, mimeType: string): boolean {
  return isEditable(mimeType) && bytes <= FILE_SIZE_LIMITS.EDIT * 1024 * 1024;
}

/**
 * Generate unique filename to avoid collisions.
 */
export function generateUniqueFilename(filename: string, existingFiles: string[]): string {
  if (!existingFiles.includes(filename)) {
    return filename;
  }

  const ext = getFileExtension(filename);
  const nameWithoutExt = getFileNameWithoutExtension(filename);
  let counter = 1;

  while (true) {
    const newName = ext
      ? `${nameWithoutExt} (${counter}).${ext}`
      : `${nameWithoutExt} (${counter})`;

    if (!existingFiles.includes(newName)) {
      return newName;
    }
    counter++;
  }
}
