import type { FC } from 'react';

interface Props {
  value: string;
  onChange: (value: string) => void;
}

const tabs = [
  { id: 'inbox', label: 'Inbox' },
  { id: 'drafts', label: 'Draft Review' },
  { id: 'settings', label: 'Settings' },
];

export const NavTabs: FC<Props> = ({ value, onChange }) => {
  return (
    <div className="tabs">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={value === tab.id ? 'tab active' : 'tab'}
          onClick={() => onChange(tab.id)}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};
