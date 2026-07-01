import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import App from '../src/App'

describe('App', () => {
	it('renders the main shell with Go button disabled until resume input exists', () => {
		render(<App />)

		expect(
			screen.getByRole('heading', { name: 'Aptitude Search' }),
		).toBeInTheDocument()
		expect(screen.getByRole('button', { name: 'Go →' })).toBeDisabled()
	})

	it('enables Go button after pasting resume text', async () => {
		const user = userEvent.setup()

		render(<App />)

		await user.click(screen.getByRole('button', { name: 'Paste resume' }))
		await user.type(
			screen.getByPlaceholderText('Paste resume text...'),
			'Alex Morgan — software engineer',
		)

		await waitFor(() => {
			expect(screen.getByRole('button', { name: 'Go →' })).toBeEnabled()
		})
	})

	it('advances to optional criteria after Go with resume input', async () => {
		const user = userEvent.setup()

		render(<App />)

		await user.click(screen.getByRole('button', { name: 'Paste resume' }))
		await user.type(
			screen.getByPlaceholderText('Paste resume text...'),
			'Alex Morgan — software engineer',
		)
		await user.click(screen.getByRole('button', { name: 'Go →' }))

		expect(
			screen.getByRole('heading', { name: 'Optional search criteria' }),
		).toBeInTheDocument()
		expect(screen.getByLabelText('Location')).toBeInTheDocument()
	})

	it('enables Go button after uploading a PDF resume', async () => {
		render(<App />)

		const input = document.getElementById('resume-file') as HTMLInputElement
		const file = new File(['pdf-content'], 'career-changer-mixed-stack.pdf', {
			type: 'application/pdf',
		})
		fireEvent.change(input, { target: { files: [file] } })

		await waitFor(() => {
			expect(
				screen.getByText('career-changer-mixed-stack.pdf'),
			).toBeInTheDocument()
			expect(
				screen.getByText(
					/PDF resume attached\. Text will be extracted on the server/,
				),
			).toBeInTheDocument()
			expect(screen.getByRole('button', { name: 'Go →' })).toBeEnabled()
		})
	})
})
