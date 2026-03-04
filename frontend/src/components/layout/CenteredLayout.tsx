import { Outlet } from 'react-router-dom'

export default function CenteredLayout() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', background: 'var(--bg-body)', padding: '1rem'
    }}>
      <Outlet />
    </div>
  )
}
