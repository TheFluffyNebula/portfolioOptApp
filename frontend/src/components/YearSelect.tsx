'use client'

import { useEffect, useState } from 'react'
import { Label, Listbox, ListboxButton, ListboxOption, ListboxOptions } from '@headlessui/react'
import { ChevronUpDownIcon } from '@heroicons/react/16/solid'
import { CheckIcon } from '@heroicons/react/20/solid'

const list = [
    { id: 1, label: '2007', value: 2007 },
    { id: 2, label: '2008', value: 2008 },
    { id: 3, label: '2009', value: 2009 },
    { id: 4, label: '2010', value: 2010 },
    { id: 5, label: '2011', value: 2011 },
    { id: 6, label: '2012', value: 2012 },
    { id: 7, label: '2013', value: 2013 },
];

interface YearSelectInterface {
    label: string;
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
    start: boolean;
}

const YearSelect = (props: YearSelectInterface) => {
    const [selected, setSelected] = useState(list[0]);

    useEffect(() => {
        if (props.start) {
            props.setState({ ...props.state, start_year: selected.value, wind: [], wave: [], kite: [], coaxial: [] });
        } else {
            props.setState({ ...props.state, end_year: selected.value, wind: [], wave: [], kite: [], coaxial: [] });
        }
    }, [selected]);

    return (
        <Listbox value={selected} onChange={setSelected}>
            <div>
                <Label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                    {props.label}
                </Label>
                <div className="relative mt-0 w-full">
                    <ListboxButton
                        className="grid w-full cursor-default grid-cols-1 rounded-lg py-2 pl-3 pr-2 text-left text-sm focus:outline-none"
                        style={{
                            background: 'var(--surface-2)',
                            border: '1px solid rgba(255,255,255,0.08)',
                            color: 'var(--foreground)',
                        }}
                    >
                        <span className="col-start-1 row-start-1 flex items-center gap-3 pr-6">
                            <span className="block truncate">{selected.label}</span>
                        </span>
                        <ChevronUpDownIcon
                            aria-hidden="true"
                            className="col-start-1 row-start-1 size-4 self-center justify-self-end"
                            style={{ color: 'var(--muted)' }}
                        />
                    </ListboxButton>

                    <ListboxOptions
                        transition
                        className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-lg py-1 text-sm shadow-xl focus:outline-none data-[closed]:data-[leave]:opacity-0 data-[leave]:transition data-[leave]:duration-100 data-[leave]:ease-in"
                        style={{
                            background: '#111F33',
                            border: '1px solid rgba(255,255,255,0.1)',
                        }}
                    >
                        {list.map((elem) => (
                            <ListboxOption
                                key={elem.id}
                                value={elem}
                                className="group relative cursor-default select-none py-2 pl-3 pr-9 data-[focus]:bg-white/5"
                                style={{ color: 'var(--foreground)' }}
                            >
                                <span className="ml-1 block truncate font-normal group-data-[selected]:font-semibold">
                                    {elem.label}
                                </span>
                                <span
                                    className="absolute inset-y-0 right-0 flex items-center pr-4 group-[&:not([data-selected])]:hidden"
                                    style={{ color: 'var(--accent)' }}
                                >
                                    <CheckIcon aria-hidden="true" className="size-4" />
                                </span>
                            </ListboxOption>
                        ))}
                    </ListboxOptions>
                </div>
            </div>
        </Listbox>
    );
};

export default YearSelect;
