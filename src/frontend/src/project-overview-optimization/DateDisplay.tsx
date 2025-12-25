/**
 * DateDisplay Component
 * Requirements: 8.1, 8.3, 8.4, 8.5
 */

import React from 'react';
import { DateFormatterProps } from '../types/project-overview';
import { CSS_CLASSES, DATE_DISPLAY_FONT_SIZE, CARD_ELEMENT_MARGIN } from '../constants/project-overview';
import { formatProjectDate } from '../utils/project-overview';
import './DateDisplay.css';

export const DateDisplay: React.FC<DateFormatterProps> = ({
  date,
  className = '',
}) => {
  const formattedDate = formatProjectDate(date);

  return (
    <span
      className={`
        ${CSS_CLASSES.dateDisplay}
        ${className}
      `.trim()}
      style={{
        fontSize: `${DATE_DISPLAY_FONT_SIZE}px`,
        marginBottom: `${CARD_ELEMENT_MARGIN}px`,
      }}
      title={`最后更新: ${formattedDate}`}
      aria-label={`最后更新时间: ${formattedDate}`}
    >
      {formattedDate}
    </span>
  );
};

export default DateDisplay;