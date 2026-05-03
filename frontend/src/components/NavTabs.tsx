import type { FC } from 'react';

interface Props {
  value: string;
  onChange: (value: string) => void;
}

const tabs = [
  { id: 'inbox', label: '📥 Входящие' },
  { id: 'drafts', label: '📝 Черновики' },
  { id: 'settings', label: '⚙️ Настройки' },
];

export const NavTabs: FC<Props> = ({ value, onChange }) => {
  return (
    <nav className="bottom-nav" aria-label="Основная навигация">
      {tabs.map((tab) => {
        const [emoji, label] = tab.label.split(' ');
        return (
          <button
            key={tab.id}
            className={value === tab.id ? 'bottom-nav-tab active' : 'bottom-nav-tab'}
            onClick={() => onChange(tab.id)}
            type="button"
          >
            <span>{emoji}</span>
            <span>{label}</span>
          </button>
        );
      })}
    </nav>
  );
};
