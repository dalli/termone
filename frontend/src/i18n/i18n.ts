export const translations = {
  en: {
    app: {
      title: 'Termone',
      description: 'SSH Infrastructure Management',
    },
    nav: {
      dashboard: 'Dashboard',
      hosts: 'Hosts',
      terminal: 'Terminal',
      files: 'Files',
      stats: 'Stats',
      admin: 'Admin',
    },
  },
  ko: {
    app: {
      title: 'Termone',
      description: 'SSH 인프라 관리',
    },
    nav: {
      dashboard: '대시보드',
      hosts: '호스트',
      terminal: '터미널',
      files: '파일',
      stats: '통계',
      admin: '관리',
    },
  },
};

export const useTranslation = (lang: 'en' | 'ko' = 'en') => {
  return translations[lang];
};
