import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  Shield,
  GitBranch,
  Container,
  Brain,
  FlaskConical,
  FileText,
  ChevronRight,
  CheckCircle,
  ArrowRight,
  Star,
  Menu,
  X,
} from 'lucide-react'
import { useState } from 'react'

const features = [
  {
    icon: GitBranch,
    title: '1. Récupération du code',
    description: 'Depuis votre dépôt Git, un fichier ZIP ou directement via une URL. SAST IA clone ou télécharge votre code source en toute sécurité.',
  },
  {
    icon: Container,
    title: '2. Conteneurisation Docker',
    description: 'Votre application est déployée dans un environnement Docker isolé. Aucun impact sur votre infrastructure, test en conditions réelles.',
  },
  {
    icon: Brain,
    title: '3. Analyse IA multi-couche',
    description: 'Scan statique OWASP Top 10 (XSS, SQLi, CSRF, IDOR) + analyse avancée (RCE, buffer overflow, attaques BDD). L\'IA explore chaque recoin.',
  },
  {
    icon: FlaskConical,
    title: '4. Validation active des vulnérabilités',
    description: 'Chaque finding est automatiquement testé sur le container : les faux positifs sont éliminés, seules les vulnérabilités réellement exploitables remontent.',
  },
  {
    icon: FileText,
    title: '5. Rapport avec résultats validés',
    description: 'Un rapport clair, précis : fichier:ligne, score CVSS, reproduction pas-à-pas, correctif recommandé. Zéro bruit, que des résultats utiles.',
  },
]

const stats = [
  { value: '98%', label: 'De faux positifs éliminés' },
  { value: '< 60 min', label: 'Audit complet avec validation' },
  { value: '4.9/5', label: 'Satisfaction client' },
  { value: 'OWASP', label: 'Top 10 couvert' },
]

export default function Landing() {
  const { user } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary-600" />
              <span className="text-xl font-bold gradient-text">SAST IA</span>
            </div>

            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm font-medium text-gray-600 hover:text-gray-900">Fonctionnalités</a>
              <a href="#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900">Tarifs</a>
              <a href="#testimonials" className="text-sm font-medium text-gray-600 hover:text-gray-900">Avis</a>
            </div>

            <div className="hidden md:flex items-center gap-3">
              {user ? (
                <Link to="/dashboard" className="btn-primary text-sm">
                  Tableau de bord
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Link>
              ) : (
                <>
                  <Link to="/login" className="btn-outline text-sm">Connexion</Link>
                  <Link to="/register" className="btn-primary text-sm">
                    Essayer gratuitement
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                </>
              )}
            </div>

            <button
              className="md:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-100 bg-white px-4 py-4 space-y-3">
            <a href="#features" className="block text-sm font-medium text-gray-600 py-2">Fonctionnalités</a>
            <a href="#pricing" className="block text-sm font-medium text-gray-600 py-2">Tarifs</a>
            <a href="#testimonials" className="block text-sm font-medium text-gray-600 py-2">Avis</a>
            {user ? (
              <Link to="/dashboard" className="btn-primary w-full text-center text-sm">Tableau de bord</Link>
            ) : (
              <div className="space-y-2 pt-2">
                <Link to="/login" className="btn-outline w-full text-center text-sm block">Connexion</Link>
                <Link to="/register" className="btn-primary w-full text-center text-sm block">Essayer gratuitement</Link>
              </div>
            )}
          </div>
        )}
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 lg:pt-40 lg:pb-28 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-50 via-white to-teal-50" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-200/30 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-200/30 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-50 border border-cyan-200 rounded-full text-sm font-medium text-cyan-700 mb-8">
                <Star className="w-4 h-4" />
                Validation Docker incluse — zéro faux positif
              </div>

            <h1 className="text-5xl lg:text-7xl font-extrabold text-gray-900 tracking-tight mb-8">
              Du dépôt au rapport
              <span className="block gradient-text mt-2">validé sans faux positifs</span>
            </h1>

            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10 leading-relaxed">
              SAST IA clone votre code, le déploie dans un container Docker isolé, lance une analyse IA
              multi-couche, puis <strong>valide chaque vulnérabilité en conditions réelles</strong>.
              Résultat : zéro faux positifs, des correctifs que vous pouvez appliquer en confiance.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              {user ? (
                <Link to="/dashboard" className="btn-primary text-lg px-8 py-4">
                  Accéder à mon tableau de bord
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn-primary text-lg px-8 py-4">
                    Commencer un audit gratuit
                    <ChevronRight className="w-5 h-5 ml-2" />
                  </Link>
                  <a href="#features" className="btn-outline text-lg px-8 py-4">
                    Voir les fonctionnalités
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-white border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl lg:text-4xl font-bold gradient-text">{stat.value}</p>
                <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Le pipeline complet
              <span className="block gradient-text">de l'analyse à la validation</span>
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              De la récupération du code jusqu'au rapport final, chaque étape est automatisée pour vous offrir
              des résultats fiables, sans bruit.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div key={feature.title} className="bg-white rounded-2xl p-8 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center mb-5">
                  <feature.icon className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Comment ça fonctionne
            </h2>
            <p className="text-lg text-gray-600">Architecture automatisée en 5 étapes</p>
          </div>

          <div className="relative">
            <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-200 via-teal-300 to-cyan-200 hidden lg:block -translate-y-1/2" />
            <div className="grid md:grid-cols-5 gap-6">
              {[
                { step: '01', title: 'Code source', desc: 'Git / upload / URL' },
                { step: '02', title: 'Container Docker', desc: 'Environnement isolé' },
                { step: '03', title: 'Scan IA', desc: 'OWASP + RCE + BDD' },
                { step: '04', title: 'Validation', desc: 'Tests réels, 0 faux positif' },
                { step: '05', title: 'Rapport', desc: 'CVSS, correction, PDF' },
              ].map((item, i) => (
                <div key={item.step} className="relative text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-cyan-500/20">
                    <span className="text-xl font-bold text-white">{item.step}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-500">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Tarif unique, complet
            </h2>
            <p className="text-lg text-gray-600">Analyse de code + validation Docker, tout compris</p>
          </div>

          <div className="max-w-lg mx-auto">
            <div className="relative bg-white rounded-2xl p-8 border-2 border-cyan-500 shadow-xl shadow-cyan-500/10">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-cyan-600 to-teal-700 text-white text-sm font-medium rounded-full">
                L'essentiel
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2 mt-4">Audit Complet</h3>
              <p className="text-gray-500 mb-6">Analyse statique + validation Docker avec tests d'exploitabilité réels</p>
              <p className="text-4xl font-bold text-gray-900 mb-6">
                99€
                <span className="text-lg font-normal text-gray-500">/audit</span>
              </p>
              <ul className="space-y-3 mb-8">
                {[
                  'Analyse complète du code source',
                  'Détection OWASP Top 10 + RCE, buffer overflow, etc.',
                  'Déploiement Docker automatisé pour tests réels',
                  'Validation active de chaque vulnérabilité',
                  'Élimination des faux positifs — résultats exploitables uniquement',
                  'Rapport détaillé : fichier:ligne, CVSS, reproduction, correction',
                  'Export PDF pour audits de conformité',
                  'Code supprimé après analyse (RGPD)',
                ].map((f) => (
                  <li key={f} className="flex items-start gap-3 text-sm text-gray-600">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                to={user ? "/audits/new" : "/register"}
                className="w-full flex items-center justify-center px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-cyan-600 to-teal-700 hover:from-cyan-700 hover:to-teal-800 shadow-lg shadow-cyan-600/25 transition-all"
              >
                {user ? 'Lancer un audit' : 'Commencer'}
                <ChevronRight className="w-4 h-4 ml-1" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-gradient-to-br from-cyan-600 to-teal-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Prêt à sécuriser vos applications ?
          </h2>
          <p className="text-xl text-cyan-100 mb-10 max-w-2xl mx-auto">
            Dites adieu aux faux positifs. Un audit complet, du dépôt au rapport validé.
          </p>
          <Link
            to={user ? "/audits/new" : "/register"}
            className="inline-flex items-center px-8 py-4 rounded-xl bg-white text-cyan-700 font-semibold text-lg hover:bg-cyan-50 transition-colors shadow-xl"
          >
            {user ? 'Lancer mon premier audit' : 'Essayer gratuitement'}
            <ArrowRight className="w-5 h-5 ml-2" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-cyan-400" />
              <span className="text-lg font-bold text-white">SAST IA</span>
            </div>
            <p className="text-sm">&copy; 2026 SAST IA. Tous droits réservés.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
