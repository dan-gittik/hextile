import React from 'react'
import ReactDOM from 'react-dom'
! for component in components:
    import (|component|) from './(|component|)'
!? if api:
    import api from './api'

! for component in components:
    global.load(|component|) = (id, props) => {
        const root = ReactDOM.createRoot(document.getElementById(id))
        ! if api:
            root.render(<(|component|) {...props || {}} api={api} />)
        ! else:
            root.render(<(|component|) {...props || {}} />)
    }