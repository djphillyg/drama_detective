import { render, screen } from '@testing-library/react';
import { ConfidenceSlider } from './ConfidenceSlider';

describe('ConfidenceSlider', () => {
  test('renders slider with title and labels', () => {
    const mockOnChange = jest.fn();

    render(<ConfidenceSlider value={60} onChange={mockOnChange} />);

    // Check that the title is present
    expect(screen.getByText('How confident should the detective be?')).toBeInTheDocument();

    // Check that the labels are present
    expect(screen.getByText('get loose with it')).toBeInTheDocument();
    expect(screen.getByText('stick to the facts')).toBeInTheDocument();

    // Check that the slider input exists
    const slider = screen.getByRole('slider');
    expect(slider).toBeInTheDocument();
  });

  test('renders slider with correct value', () => {
    const mockOnChange = jest.fn();

    render(<ConfidenceSlider value={60} onChange={mockOnChange} />);

    const slider = screen.getByRole('slider');

    // Verify slider has correct current value
    expect(slider.getAttribute('aria-valuenow')).toBe('60');
  });

  test('slider has correct min and max values (30-90)', () => {
    const mockOnChange = jest.fn();

    render(<ConfidenceSlider value={60} onChange={mockOnChange} />);

    const slider = screen.getByRole('slider') as HTMLInputElement;

    expect(slider.getAttribute('aria-valuemin')).toBe('30');
    expect(slider.getAttribute('aria-valuemax')).toBe('90');
  });
});
