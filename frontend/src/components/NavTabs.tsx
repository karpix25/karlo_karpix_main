import type { FC } from 'react';

interface Props {
  value: string;
  onChange: (value: string) => void;
}

const tabs = [
  { id: 'inbox', label: 'Входящие', icon: '📥' },
  { id: 'drafts', label: 'Черновики', icon: '📝' },
  { id: 'settings', label: 'Настройки', icon: '⚙️' },
];

export const NavTabs: FC<Props> = ({ value, onChange }) => {
  return (
    <nav className="bottom-nav" aria-label="Основная навигация">
      {tabs.map((tab) => {
        return (
          <button
            key={tab.id}
            className={value === tab.id ? 'bottom-nav-tab active' : 'bottom-nav-tab'}
            onClick={() => onChange(tab.id)}
            type="button"
          >
            <span style={{ fontSize: '20px' }}>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
};
