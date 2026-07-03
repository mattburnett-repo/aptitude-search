import type { ReactNode } from 'react'
import { hasSupportLink } from '../config/support'
import { BuyMeACoffeeButton } from './BuyMeACoffeeButton'
import { SupportLink } from './SupportLink'
import type { Theme } from '../hooks/useTheme'

function ThemeToggleIcon({ theme }: { theme: Theme }) {
	if (theme === 'light') {
		return (
			<svg
				aria-hidden="true"
				className="theme-toggle-icon"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				strokeWidth="2"
				strokeLinecap="round"
				strokeLinejoin="round"
			>
				<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
			</svg>
		)
	}

	return (
		<svg
			aria-hidden="true"
			className="theme-toggle-icon"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<circle cx="12" cy="12" r="4" />
			<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
		</svg>
	)
}

export function SiteBackdrop({ intense }: { intense: boolean }) {
	return (
		<div
			className={[
				'site-backdrop',
				intense ? 'site-backdrop-intense' : 'site-backdrop-calm',
			].join(' ')}
			aria-hidden="true"
		>
			<div className="site-backdrop-glow site-backdrop-glow--primary" />
			<div className="site-backdrop-glow site-backdrop-glow--secondary" />
			<div className="site-backdrop-glow site-backdrop-glow--center" />
			{intense && <div className="site-backdrop-vignette" />}
			<svg
				className="site-backdrop-blob site-backdrop-blob--a"
				viewBox="0 0 200 200"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					fill="currentColor"
					d="M44.7,-58.3C57.9,-47.4,67.8,-32.1,71.8,-15.2C75.8,1.7,73.9,20.2,64.8,34.8C55.7,49.4,39.4,60.1,21.8,66.8C4.2,73.5,-14.7,76.2,-31.4,70.1C-48.1,64,-62.6,49.1,-70.4,31.8C-78.2,14.5,-79.3,-5.2,-73.1,-22.4C-66.9,-39.6,-53.4,-54.3,-37.8,-64.4C-22.2,-74.5,-4.5,-80,-11.3,-67.4C-18.1,-54.8,31.5,-69.2,44.7,-58.3Z"
					transform="translate(100 100)"
				/>
			</svg>
			<svg
				className="site-backdrop-blob site-backdrop-blob--b"
				viewBox="0 0 200 200"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					fill="currentColor"
					d="M39.5,-50.2C50.9,-38.8,59.2,-24.1,62.4,-8.5C65.6,7.1,63.7,23.6,55.2,36.8C46.7,50,31.6,59.9,15.1,64.2C-1.4,68.5,-18.3,67.2,-33.1,60.1C-47.9,53,-60.6,40.1,-67.4,24.5C-74.2,8.9,-75.1,-9.3,-68.9,-25.1C-62.7,-40.9,-49.4,-54.3,-34.1,-62.1C-18.8,-69.9,-1.5,-72.1,12.8,-66.8C27.1,-61.5,28.1,-61.6,39.5,-50.2Z"
					transform="translate(100 100)"
				/>
			</svg>
			<svg
				className="site-backdrop-blob site-backdrop-blob--c"
				viewBox="0 0 200 200"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					fill="currentColor"
					d="M44.7,-58.3C57.9,-47.4,67.8,-32.1,71.8,-15.2C75.8,1.7,73.9,20.2,64.8,34.8C55.7,49.4,39.4,60.1,21.8,66.8C4.2,73.5,-14.7,76.2,-31.4,70.1C-48.1,64,-62.6,49.1,-70.4,31.8C-78.2,14.5,-79.3,-5.2,-73.1,-22.4C-66.9,-39.6,-53.4,-54.3,-37.8,-64.4C-22.2,-74.5,-4.5,-80,-11.3,-67.4C-18.1,-54.8,31.5,-69.2,44.7,-58.3Z"
					transform="translate(100 100)"
				/>
			</svg>
		</div>
	)
}

export function SiteHeader({
	theme,
	onToggleTheme,
}: {
	theme: Theme
	onToggleTheme: () => void
}) {
	return (
		<header className="site-header">
			<div className="site-header-inner">
				<a className="site-brand" href="/">
					<span className="site-brand-mark" aria-hidden="true" />
					<h1 className="site-brand-text">Aptitude Search</h1>
				</a>
				<button
					type="button"
					className="theme-toggle"
					onClick={onToggleTheme}
					aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
				>
					<ThemeToggleIcon theme={theme} />
				</button>
			</div>
		</header>
	)
}

export function SiteFooter() {
	return (
		<footer className="site-footer">
			<div className="site-footer-inner">
				<p className="site-footer-copy">
					Aptitude Search — beyond the obvious job search.
				</p>
				{hasSupportLink && (
					<div className="site-footer-support">
						<BuyMeACoffeeButton />
					</div>
				)}
			</div>
		</footer>
	)
}

export function SiteShell({
	mode,
	children,
}: {
	mode: 'marketing' | 'tool'
	children: ReactNode
}) {
	return (
		<div className={`site-shell site-shell--${mode}`}>
			<SiteBackdrop intense={mode === 'marketing'} />
			{children}
		</div>
	)
}

export function InputTrustNotes() {
	return (
		<ul className="input-trust-notes" aria-label="Privacy and pricing">
			<li>
				We don&apos;t harvest, sell, save or otherwise keep any of your
				information.
			</li>
			<li>
				It doesn&apos;t cost you anything to use this tool, but{' '}
				<SupportLink>donations</SupportLink> are always appreciated.
			</li>
		</ul>
	)
}

export function InputHero() {
	return (
		<section className="site-hero" aria-labelledby="site-hero-title">
			<p className="site-hero-eyebrow">Beyond the obvious job searches</p>
			<h2 id="site-hero-title" className="site-hero-title">
				Find work that fits your real strengths
			</h2>
			<p className="site-hero-lead">
				Discover non-obvious job search paths from your resume: aptitudes,
				career matches, target roles, and verified postings — all in one go.
			</p>
		</section>
	)
}
