import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/20/solid'

interface ResourceSelectInterface {
    state: {
        wind: string[];
        wave: string[];
        kite: string[];
        coaxial: string[];
        transmission: string[];
        lcoe_max: number;
        lcoe_min: number;
        lcoe_step: number;
        start_year: number;
        end_year: number;
    };
    setState: any;
}

export default function ResourceSelect(props: ResourceSelectInterface) {
    const windDesigns = ["8MW Vestas 2020", "12MW 2030", "15MW 2030", "18MW 2030"];
    const kiteDesigns = ["0.05MW (0.5m/s)", "0.14MW (0.75m/s)", "0.31MW (1.0m/s)", "0.57MW (1.25m/s)", "0.93MW (1.5m/s)", "1.43MW (1.75m/s)", "2.04MW (2.0m/s)", "1.987MW (2.25m/s)", "1.87MW (2.5m/s)", "1.81MW (2.75m/s)"];
    const waveDesigns = ["Pelamis", "RM3"];
    const coaxialDesigns = ["0.6MW (1.0m/s)", "1.0MW (1.5m/s)", "1.75MW (1.75m/s)", "2.0MW (1.75m/s)", "1.5MW (1.5m/s)"];

    interface dictInterface { [key: string]: string }

    const dict: dictInterface = {
        "8MW Vestas 2020": `Wind/Upscale3h_0.1Degree_${props.state.start_year}_${props.state.end_year}_GenCost_ATB_8MW_2020_Vestas.npz`,
        "12MW 2030": `Wind/Upscale3h_0.1Degree_${props.state.start_year}_${props.state.end_year}_GenCost_ATB_12MW_2030.npz`,
        "15MW 2030": `Wind/Upscale3h_0.1Degree_${props.state.start_year}_${props.state.end_year}_GenCost_ATB_15MW_2030.npz`,
        "18MW 2030": `Wind/Upscale3h_0.1Degree_${props.state.start_year}_${props.state.end_year}_GenCost_ATB_18MW_2030.npz`,
        "0.05MW (0.5m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS0.5_${props.state.start_year}_${props.state.end_year}.npz`,
        "0.14MW (0.75m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS0.75_${props.state.start_year}_${props.state.end_year}.npz`,
        "0.31MW (1.0m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS1.0_${props.state.start_year}_${props.state.end_year}.npz`,
        "0.57MW (1.25m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS1.25_${props.state.start_year}_${props.state.end_year}.npz`,
        "0.93MW (1.5m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS1.5_${props.state.start_year}_${props.state.end_year}.npz`,
        "1.43MW (1.75m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS1.75_${props.state.start_year}_${props.state.end_year}.npz`,
        "2.04MW (2.0m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS2.0_${props.state.start_year}_${props.state.end_year}.npz`,
        "1.987MW (2.25m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS2.25_${props.state.start_year}_${props.state.end_year}.npz`,
        "1.87MW (2.5m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS2.5_${props.state.start_year}_${props.state.end_year}.npz`,
        "1.81MW (2.75m/s)": `OceanCurrent/PowerTimeSeriesKite_VD50_BCS2.75_${props.state.start_year}_${props.state.end_year}.npz`,
        "Pelamis": `Wave/${props.state.start_year}_${props.state.end_year}_Pelamis.npz`,
        "RM3": `Wave/${props.state.start_year}_${props.state.end_year}_RM3.npz`,
        "0.6MW (1.0m/s)": "",
    };

    const resourceGroups: { label: string; key: 'wind' | 'kite' | 'wave' | 'coaxial'; designs: string[] }[] = [
        { label: 'Wind',    key: 'wind',    designs: windDesigns },
        { label: 'Kite',    key: 'kite',    designs: kiteDesigns },
        { label: 'Wave',    key: 'wave',    designs: waveDesigns },
        { label: 'Coaxial', key: 'coaxial', designs: coaxialDesigns },
    ];

    const handleToggle = (key: 'wind' | 'kite' | 'wave' | 'coaxial', val: string) => {
        const current: string[] = props.state[key];
        const path = dict[val];
        const updated = current.includes(path)
            ? current.filter(e => e !== path)
            : [...current, path];
        props.setState({ ...props.state, [key]: updated });
    };

    const totalSelected = ['wind', 'kite', 'wave', 'coaxial'].reduce(
        (sum, k) => sum + (props.state[k as keyof typeof props.state] as string[]).length, 0
    );

    return (
        <Menu as="div" className="relative inline-block text-left w-full">
            <MenuButton
                className="inline-flex items-center justify-between gap-2 w-full rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5"
                style={{
                    background: 'var(--surface-2)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    color: 'var(--foreground)',
                }}
            >
                <span>
                    {totalSelected === 0
                        ? 'Select devices'
                        : `${totalSelected} device${totalSelected !== 1 ? 's' : ''} selected`}
                </span>
                <ChevronDownIcon className="size-4 flex-shrink-0" style={{ color: 'var(--muted)' }} />
            </MenuButton>

            <MenuItems
                transition
                className="absolute z-20 mt-2 w-full origin-top-right rounded-xl p-5 shadow-2xl focus:outline-none data-[closed]:scale-95 data-[closed]:transform data-[closed]:opacity-0 data-[enter]:duration-100 data-[leave]:duration-75 data-[enter]:ease-out data-[leave]:ease-in"
                style={{
                    background: '#111F33',
                    border: '1px solid rgba(255,255,255,0.1)',
                    minWidth: '480px',
                }}
            >
                {resourceGroups.map(({ label, key, designs }) => (
                    <div key={key} className="mb-5 last:mb-0">
                        <div className="flex items-center gap-2 mb-3">
                            <span className="text-xs font-semibold" style={{ color: 'var(--accent)' }}>{label}</span>
                            <div className="flex-1 h-px" style={{ background: 'rgba(0,191,99,0.2)' }} />
                        </div>
                        <div className="grid grid-cols-3 gap-x-6 gap-y-2">
                            {designs.map(elem => (
                                <label key={elem} className="flex items-center gap-2 cursor-pointer group">
                                    <input
                                        type="checkbox"
                                        className="shrink-0 rounded border"
                                        style={{ accentColor: 'var(--accent)' }}
                                        checked={props.state[key].includes(dict[elem])}
                                        onChange={() => handleToggle(key, elem)}
                                    />
                                    <span className="text-xs group-hover:opacity-100 transition-opacity" style={{ color: 'var(--muted)' }}>
                                        {elem}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>
                ))}
            </MenuItems>
        </Menu>
    );
}
