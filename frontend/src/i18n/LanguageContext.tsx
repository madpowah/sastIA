import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { translations, Lang } from './translations'

type NestedKeyOf<T> = T extends object
  ? { [K in keyof T]: K extends string
    ? T[K] extends object
      ? `${K}.${NestedKeyOf<T[K]>}`
      : K
    : never }[keyof T]
  : never

type TKey = NestedKeyOf<typeof translations.en>

interface LanguageContextType {
  lang: Lang
  setLang: (lang: Lang) => void
  t: (key: TKey) => string
}

const STORAGE_KEY = 'sastia_lang'

const LanguageContext = createContext<LanguageContextType>({
  lang: 'en',
  setLang: () => {},
  t: (key: string) => key,
})

function resolvePath(obj: any, path: string): string {
  const keys = path.split('.')
  let result = obj
  for (const key of keys) {
    if (result == null) return path
    result = result[key]
  }
  return typeof result === 'string' ? result : path
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'fr' || stored === 'en') return stored
    return 'en'
  })

  const setLang = useCallback((newLang: Lang) => {
    setLangState(newLang)
    localStorage.setItem(STORAGE_KEY, newLang)
  }, [])

  const t = useCallback((key: TKey): string => {
    const dict = translations[lang] || translations.en
    return resolvePath(dict, key)
  }, [lang])

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  return useContext(LanguageContext)
}
