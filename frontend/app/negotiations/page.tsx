"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { negotiationApi } from "@/lib/api";
import type { Negotiation } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, MessageSquare, Clock, CheckCircle2, XCircle, Building2 } from "lucide-react";
import { NegotiationRequestModal } from "@/components/negotiations/NegotiationRequestModal";
import { useAuth } from "@/contexts/AuthContext";

type StatusFilter = "all" | "pending" | "active" | "completed" | "rejected" | "cancelled";

export default function NegotiationsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [negotiations, setNegotiations] = useState<Negotiation[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadNegotiations();
  }, [statusFilter]);

  const loadNegotiations = async () => {
    try {
      setLoading(true);
      const response = await negotiationApi.listNegotiations(
        statusFilter === "all" ? undefined : statusFilter
      );
      setNegotiations(response.negotiations);
    } catch (error) {
      console.error("Failed to load negotiations:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: Negotiation["status"]) => {
    const variants: Record<Negotiation["status"], { variant: any; icon: any; label: string }> = {
      pending: { variant: "secondary", icon: Clock, label: "Pending" },
      active: { variant: "default", icon: MessageSquare, label: "Active" },
      completed: { variant: "default", icon: CheckCircle2, label: "Completed" },
      rejected: { variant: "destructive", icon: XCircle, label: "Rejected" },
      cancelled: { variant: "outline", icon: XCircle, label: "Cancelled" },
    };

    const config = variants[status];
    const Icon = config.icon;

    return (
      <Badge variant={config.variant as any} className="gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const getOtherParty = (negotiation: Negotiation) => {
    if (!user) return null;
    return negotiation.initiator_user_id === user.id
      ? negotiation.receiver
      : negotiation.initiator;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Negotiations</h1>
          <p className="text-gray-500 mt-1">
            Manage contract negotiations with other companies
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} size="lg">
          <Plus className="h-5 w-5 mr-2" />
          New Negotiation
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {(["all", "active", "pending", "completed"] as StatusFilter[]).map((filter) => (
          <Button
            key={filter}
            variant={statusFilter === filter ? "default" : "outline"}
            size="sm"
            onClick={() => setStatusFilter(filter)}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
          </Button>
        ))}
      </div>

      {/* Negotiations List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-2/3" />
                <Skeleton className="h-4 w-1/2 mt-2" />
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : negotiations.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <MessageSquare className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No negotiations yet
            </h3>
            <p className="text-gray-500 text-center mb-4">
              Start a new negotiation with another company to begin discussing contract
              terms.
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create First Negotiation
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {negotiations.map((negotiation) => {
            const otherParty = getOtherParty(negotiation);

            return (
              <Card
                key={negotiation.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/negotiations/${negotiation.id}`)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <CardTitle className="text-xl">
                          {negotiation.contract_name}
                        </CardTitle>
                        {getStatusBadge(negotiation.status)}
                        {negotiation.unread_count && negotiation.unread_count > 0 && (
                          <Badge variant="destructive" className="ml-2">
                            {negotiation.unread_count} unread
                          </Badge>
                        )}
                      </div>
                      <CardDescription className="flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        {otherParty?.company_name || "Unknown Company"}
                      </CardDescription>
                    </div>
                    <div className="text-right text-sm text-gray-500">
                      <div>Created {formatDate(negotiation.created_at)}</div>
                      {negotiation.accepted_at && (
                        <div>Accepted {formatDate(negotiation.accepted_at)}</div>
                      )}
                    </div>
                  </div>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Negotiation Modal */}
      <NegotiationRequestModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          setShowCreateModal(false);
          loadNegotiations();
        }}
      />
    </div>
  );
}
