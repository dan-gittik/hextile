!if not api:
    % stop

% interpolate('<%', '%>')
!import json
import axios from 'axios'

class API {

    defaultHost = 'localhost'
    defaultPort = 8000
    defaultPath = '/'
    defaultSecure = false
    defaultTimeout = 10

    constructor() {
        this.host = this.defaultHost
        this.port = this.defaultPort
        this.path = this.defaultPath
        this.secure = this.defaultSecure
        this.timeout = this.defaultTimeout
        this.headers = {}
        this._token = null
        this._axios = null
    }

    client() {
        if (!this._axios) {
            this._axios = axios.create({
                baseURL: `${this.secure ? 'https' : 'http'}://${this.host}:${this.port}${this.path}`,
                timeout: this.timeout * 1000,
                headers: this.headers,
            })
        }
        return this._axios
    }

    reset() {
        this._axios = null
    }

    % modular-define typecheck name config
        !
            type, nullable = config.get('type'), False
            if isinstance(type, list):
                type, nullable = type[0], True
            if nullable:
                is_defined = f'({name} !== undefined && {name} !== null)'
            else:
                is_defined = f'({name} !== undefined)'
        !if type == 'boolean':
            <% name %> = <% is_defined %> ? Boolean(<% name %>) : null
        !elif type == 'integer':
            if <% is_defined %> {
                <% name %> = parseInt(<% name %>)
                !if 'minimum' in config:
                    if (<% name %> < <% config['minimum'] %>) {
                        throw `<% name %> must be greater than or equal to <% config['minimum'] %>`
                    }
                !if 'exclusiveMinimum' in config:
                    if (<% name %> <= <% config['exclusiveMinimum'] %>) {
                        throw `<% name %> must be greater than <% config['exclusiveMinimum'] %>`
                    }
                !if 'maximum' in config:
                    if (<% name %> > <% config['maximum'] %>) {
                        throw `<% name %> must be lesser than or equal to <% config['maximum'] %>`
                    }
                !if 'exclusiveMaximum' in config:
                    if (<% name %> >= <% config['exclusiveMaximum'] %>) {
                        throw `<% name %> must be lesser than <% config['exclusiveMaximum'] %>`
                    }
                !if 'enum' in config:
                    if (!<% json.dumps(config['enum']) %>.includes(<% name %>)) {
                        throw `invalid <% name %> ${<% name %>} (expected one of: <% ", ".join(map(str, config['enum'])) %>)`
                    }
            } else {
                <% name %> = null
            }
        !elif type == 'number':
            if <% is_defined %> {
                <% name %> = parseFloat(<% name %>)
                !if 'minimum' in config:
                    if (<% name %> < <% config['minimum'] %>) {
                        throw `<% name %> must be greater than or equal to <% config['minimum'] %>`
                    }
                !if 'exclusiveMinimum' in config:
                    if (<% name %> <= <% config['exclusiveMinimum'] %>) {
                        throw `<% name %> must be greater than <% config['exclusiveMinimum'] %>`
                    }
                !if 'maximum' in config:
                    if (<% name %> > <% config['maximum'] %>) {
                        throw `<% name %> must be lesser than or equal to <% config['maximum'] %>`
                    }
                !if 'exclusiveMaximum' in config:
                    if (<% name %> >= <% config['exclusiveMaximum'] %>) {
                        throw `<% name %> must be lesser than <% config['exclusiveMaximum'] %>`
                    }
                !if 'enum' in config:
                    if (!<% json.dumps(config['enum']) %>.includes(<% name %>)) {
                        throw `invalid <% name %> ${<% name %>} (expected one of: <% ", ".join(map(str, config['enum'])) %>)`
                    }
            } else {
                <% name %> = null
            }
        !elif type == 'string':
            if <% is_defined %> {
                <% name %> = String(<% name %>)
                !if 'pattern' in config:
                    if (!(new RegExp(<% config['pattern']!r %>)).test(<% name %>)) {
                        throw `<% name %> must match the regular expression <% config['pattern']!r %>`
                    }
                !if 'minLength' in config:
                    !if config['minLength'] == 1:
                        if (!<% name %>) {
                            throw `<% name %> cannot be empty`
                        }
                    !else:
                        if (<% name %>.length < <% config['minLength'] %>) {
                            throw `<% name %> is too short (expected a length of at least <% config['minLength'] %>, but got ${<% name %>.length})`
                        }
                !if 'maxLength' in config:
                    if (<% name %>.length > <% config['maxLength'] %>) {
                        throw `<% name %> is too long (expected a length of at most <% config['maxLength'] %>, but got ${<% name %>.length})`
                    }
                !if 'enum' in config:
                    if (!<% json.dumps(config['enum']) %>.includes(<% name %>)) {
                        throw `invalid <% name %> ${<% name %>} (expected one of: <% ", ".join(config['enum']) %>)`
                    }
            } else {
                <% name %> = null
            }
        !elif type == 'array':
            if <% is_defined %> {
                <% name %> = String(<% name %>)
                if (!Array.isArray(<% name %>)) {
                    throw `<% name %> must be an array`
                }
                !if 'minItems' in config:
                    !if config['minItems'] == 1:
                        if (!<% name %>.length) {
                            throw `<% name %> cannot be empty`
                        }
                    !else:
                        if (<% name %>.length < <% config['minItems'] %>) {
                            throw `<% name %> is too small (expected at least <% config['minItems'] %> items, but got ${<% name %>.length})`
                        }
                !if 'maxItems' in config:
                    if (<% name %>.length > <% config['maxItems'] %>) {
                        throw `<% name %> is too big (expected at most <% config['minItems'] %> items, but got ${<% name %>.length})`
                    }
                !if 'prefixItems' in config and config.get('items') is not False:
                    if (<% name %>.length < <% len(config['prefixItems']) %>) {
                        throw `<% name %> is too small (expected at least <% len(config['prefixItems']) %> items, but got ${<% name %>.length})`
                    }
                !if 'prefixItems' in config and config.get('items') is False:
                    if (<% name %>.length !== <% len(config['prefixItems']) %>) {
                        throw `<% name %> is too big (expected exactly <% len(config['prefixItems']) %> items, but got ${<% name %>.length})`
                    }
                !if 'unique' in config:
                    if (<% name %>.length !== new Set(<% name %>).size) {
                        throw `<% name %> items must be unique`
                    }
                !if 'enum' in config:
                    if (<% name %>.filter(item => !<% json.dumps(config['enum']) %>.includes(item)).length === 0) {
                        throw `invalid <% name %> ${<% name %>} (expected its items to be one of: <% ", ".join(config['enum']) %>)`
                    }
                !if isinstance(config.get('items'), dict):
                    for (let i = 0; i < <% name %>.length; i++) {
                        % modular-insert typecheck f'{name}[i]' config['items']
                    }
                !elif 'prefixItems' in config:
                    !for index, item_config in enumerate(config['prefixItems']):
                        % modular-insert typecheck f'{name}[{index}]' item_config
            } else {
                <% name %> = null
            }
        !elif type == 'object':
            if <% is_defined %> {
                if (typeof <% name %> !== 'object' || Array.isArray(<% name %>)) {
                    throw `<% name %> must be an object`
                }
                !if 'properties' in config:
                    !for item_name, item_config in config['properties'].items():
                        % modular-insert typecheck f'{name}.{item_name}' item_config
                !if 'required' in config:
                    !for item_name in config['required']:
                        !full_name = f'{name}.{item_name}'
                        if (<% full_name %> === null) {
                            throw `<% full_name %> must be provided`
                        }
            } else {
                <% name %> = null
            }
    !from encircle.web.handler import RequestHandler, WebsocketHandler, StaticDirectoryHandler, UploadDirectoryHandler, UploadHandler
    !for handler in webserver._handlers_by_path.values():
        !if isinstance(handler, RequestHandler) and handler.api:
            !for method in handler.methods:
                async <% _.camel_case(method + '_' + (handler.name or handler.function.__name__)) %>(
                    !if handler.request_schema:
                        !for param_name, param_config in handler.request_schema.json_schema['properties'].items():
                            !if 'default' in param_config:
                                <% param_name %> = <% param_config['default'] %>,
                            !else:
                                <% param_name %>,
                    !else:
                        data,
                ) {
                    !if handler.request_schema:
                        const data = {}
                        !for param_name, param_config in handler.request_schema.json_schema['properties'].items():
                            % modular-insert typecheck param_name param_config
                        !for param_name in handler.request_schema.json_schema['required']:
                            if (<% param_name %> === null) {
                                throw `<% name %> must be provided`
                            }
                            data.<% param_name %> = <% param_name %>
                    const options = {
                        url: '<% handler.path %>',
                        method: '<% method %>',
                        !if method == 'GET':
                            params: data,
                        !else:
                            data: data,
                    }
                    const response = await this.client()(options)
                    return response
                }
}

const api = new API()

export default api