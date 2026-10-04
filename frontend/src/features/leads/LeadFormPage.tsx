import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CircleAlert, LoaderCircle } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { createLead, getLead, updateLead } from './api'
import { LeadForm } from './LeadForm'
import type { LeadFormValues } from './LeadForm'
import { leadKeys } from './queryKeys'
import type { Lead, LeadPayload } from './types'

const emptyLeadForm: LeadFormValues = {
  contact_name: '',
  company: '',
  email: '',
  phone: '',
  source: '',
  status: 'NEW',
  estimated_value: '0.00',
  notes: '',
}

function leadToFormValues(lead: Lead): LeadFormValues {
  return {
    contact_name: lead.contact_name,
    company: lead.company || '',
    email: lead.email || '',
    phone: lead.phone || '',
    source: lead.source || '',
    status: lead.status,
    estimated_value: lead.estimated_value,
    notes: lead.notes || '',
  }
}

export function LeadFormPage({ mode }: { mode: 'create' | 'edit' }) {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEditing = mode === 'edit'

  const leadQuery = useQuery({
    queryKey: leadKeys.detail(id),
    queryFn: () => getLead(id),
    enabled: isEditing && Boolean(id),
    retry: false,
  })

  const mutation = useMutation({
    mutationFn: (payload: LeadPayload) =>
      isEditing ? updateLead(id, payload) : createLead(payload),
    onSuccess: async (savedLead) => {
      queryClient.setQueryData(leadKeys.detail(savedLead.id), savedLead)
      await queryClient.invalidateQueries({ queryKey: leadKeys.lists() })
      navigate(`/leads/${savedLead.id}`, { replace: true })
    },
  })

  if (isEditing && leadQuery.isPending) {
    return <PageState icon={<LoaderCircle className="size-6 animate-spin" />} text="Loading lead…" />
  }

  if (isEditing && leadQuery.isError) {
    return (
      <PageState
        icon={<CircleAlert className="size-6" />}
        text="This lead could not be found or you do not have access to it."
      />
    )
  }

  const lead = leadQuery.data

  return (
    <section className="mx-auto max-w-4xl">
      <Link
        to={lead ? `/leads/${lead.id}` : '/leads'}
        className="mb-5 inline-flex min-h-11 items-center gap-2 rounded-lg text-sm font-semibold text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        {lead ? 'Back to lead' : 'Back to leads'}
      </Link>

      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-6 sm:px-8">
          <p className="text-sm font-semibold text-blue-600">{isEditing ? 'Lead record' : 'New opportunity'}</p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
            {isEditing ? `Edit ${lead?.contact_name}` : 'Add a lead'}
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            {isEditing
              ? 'Keep contact information and sales progress accurate.'
              : 'Capture the details you need to begin the sales conversation.'}
          </p>
        </div>
        <div className="p-5 sm:p-8">
          <LeadForm
            defaultValues={lead ? leadToFormValues(lead) : emptyLeadForm}
            submitLabel={isEditing ? 'Save changes' : 'Create lead'}
            onSubmit={(payload) => mutation.mutateAsync(payload).then(() => undefined)}
          />
        </div>
      </div>
    </section>
  )
}

function PageState({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="grid min-h-[50vh] place-items-center rounded-2xl border border-slate-200 bg-white p-8 text-center">
      <div>
        <span className="mx-auto grid size-12 place-items-center rounded-full bg-slate-100 text-slate-500">{icon}</span>
        <p className="mt-4 font-medium text-slate-700">{text}</p>
        <Link to="/leads" className="mt-4 inline-flex min-h-11 items-center text-sm font-semibold text-blue-600">
          Return to leads
        </Link>
      </div>
    </div>
  )
}
