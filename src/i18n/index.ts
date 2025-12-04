import type { Lang, I18nSchema } from './types';
import { en } from './en';
import { ru } from './ru';

export const supportedLangs: Lang[] = ['en', 'ru'];
export const defaultLang: Lang = 'en';

export function getTranslations(lang: Lang): I18nSchema {
  switch (lang) {
    case 'ru':
      return ru;
    case 'en':
    default:
      return en;
  }
}

export function resolveLangFromParams(langParam: string | undefined): Lang {
  if (langParam === 'en' || langParam === 'ru') return langParam;
  return defaultLang;
}

