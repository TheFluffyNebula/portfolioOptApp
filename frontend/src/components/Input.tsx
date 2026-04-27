import React from 'react';

interface InputProps {
    label: string;
    type: string;
    placeholder?: string;
    curr: string;
    step: string;
    state?: any;
    setState?: any;
    value?: string | number;
    onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const labelMap: Record<string, string> = {
    "LCOE Min": "lcoe_min",
    "LCOE Max": "lcoe_max",
    "LCOE Step Size": "lcoe_step",
    "Max Trans. System Radius": "max_system_radius",
    "Number of Wind Devices / Resource": "WindTurbinesPerSite",
    "Number of Wind Devices / sq. km": "WindResolutionKm",
    "Number of Wave Devices / Resource": "WaveTurbinesPerSite",
    "Number of Kite Devices / Resource": "KiteTurbinesPerSite",
    "Number of Coaxial Devices / Resource": "CoaxialTurbinesPerSite",
    "Distance from Shore": "distance_from_shore",
    "Max Water Depth": "max_water_depth",
};

const Input = (props: InputProps) => {
    const key = labelMap[props.label];
    const resolvedValue = props.value !== undefined
        ? props.value
        : (props.state && key) ? props.state[key] : "";

    const onChangeHandler = (event: React.ChangeEvent<HTMLInputElement>) => {
        const rawValue = event.target.value;
        if (props.onChange) {
            props.onChange(event);
        }
        if (props.state && props.setState) {
            const k = labelMap[props.label];
            if (k) {
                const numValue = rawValue === "" ? 0 : Number(rawValue);
                props.setState({ ...props.state, [k]: numValue });
            }
        }
    };

    return (
        <div className="w-full">
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                {props.label}
            </label>
            <div
                className="flex items-center rounded-lg overflow-hidden transition-colors"
                style={{
                    background: 'var(--surface-2)',
                    border: '1px solid rgba(255,255,255,0.08)',
                }}
            >
                <input
                    type={props.type}
                    step={props.step}
                    placeholder={props.placeholder}
                    value={resolvedValue === "" ? "" : Number(resolvedValue).toString()}
                    onChange={onChangeHandler}
                    className="block min-w-0 grow py-2 px-3 text-sm bg-transparent focus:outline-none"
                    style={{ color: 'var(--foreground)' }}
                />
                {props.curr && (
                    <span
                        className="flex-shrink-0 px-3 py-2 text-xs border-l"
                        style={{ color: 'var(--muted)', borderColor: 'rgba(255,255,255,0.08)' }}
                    >
                        {props.curr}
                    </span>
                )}
            </div>
        </div>
    );
};

export default Input;
